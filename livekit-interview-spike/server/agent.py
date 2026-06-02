import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import api, rtc

from interview import InterviewEvaluator, InterviewOrchestrator
from interview.configs import TRAINING_OPTIONS
from local_providers import (
    ConversationMessage,
    DeepSeekStreamingTextProvider,
    FunAsrStreamingProvider,
    pcm_rms,
    preload_shared_funasr_model,
)
from turn_completion import TurnCompletionJudge
from turn_controller import TurnAction, TurnController


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("interview_spike.agent")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")
ROOM_NAME = os.getenv("LIVEKIT_ROOM", "interview-spike-room")
AGENT_IDENTITY = "interview-agent"


class AdaptiveVoiceGate:
    min_voice_threshold = 0.012
    voice_margin = 0.010
    speech_threshold_ratio = 2.6
    noise_smoothing = 0.985

    def __init__(self) -> None:
        self.noise_floor = 0.006

    def classify(self, rms: float) -> tuple[bool, float]:
        threshold = max(
            self.min_voice_threshold,
            self.noise_floor * self.speech_threshold_ratio,
            self.noise_floor + self.voice_margin,
        )
        has_voice = rms >= threshold
        if not has_voice:
            self.noise_floor = self.noise_floor * self.noise_smoothing + rms * (1 - self.noise_smoothing)
        return has_voice, threshold


class ConversationControl:
    def __init__(self) -> None:
        self.started = False
        self.ended = False
        self.finishing = False
        self.force_finalize = asyncio.Event()
        self.assistant_speaking = False


def create_agent_token() -> str:
    return (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(AGENT_IDENTITY)
        .with_name("AI 面试官")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=ROOM_NAME,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )


async def publish_json(room: rtc.Room, payload: dict[str, object]) -> None:
    message = json.dumps(payload, ensure_ascii=False)
    logger.info("publish data type=%s", payload.get("type"))
    await room.local_participant.publish_data(message.encode("utf-8"), reliable=True, topic="interview")


def training_config_from_event(event: dict[str, object]) -> dict[str, str]:
    config = event.get("config")
    if not isinstance(config, dict):
        config = {}
    return {
        "job_id": str(config.get("jobId", "product_manager")),
        "mode_id": str(config.get("modeId", "standard")),
        "competency_id": str(config.get("competencyId", "requirement_analysis")),
        "strategy_id": str(config.get("strategyId", "evidence_probe")),
    }


def option_label(group: str, option_id: str) -> str:
    options = TRAINING_OPTIONS.get(group, [])
    for item in options:
        if item.get("id") == option_id:
            return str(item.get("label", option_id))
    return option_id


async def main() -> None:
    logger.info("preloading FunASR model")
    await preload_shared_funasr_model()
    logger.info("FunASR model ready")

    room = rtc.Room()
    messages: list[ConversationMessage] = []
    llm_provider = DeepSeekStreamingTextProvider()
    orchestrator = InterviewOrchestrator()
    evaluator = InterviewEvaluator()
    audio_tasks: dict[str, asyncio.Task[None]] = {}
    control = ConversationControl()

    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        logger.info("participant connected identity=%s", participant.identity)

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        logger.info("track subscribed kind=%s sid=%s participant=%s", track.kind, publication.sid, participant.identity)
        if track.kind != rtc.TrackKind.KIND_AUDIO:
            return
        if participant.identity == AGENT_IDENTITY:
            return
        if publication.sid in audio_tasks and not audio_tasks[publication.sid].done():
            return
        task = asyncio.create_task(
            process_candidate_audio(room, track, publication, messages, llm_provider, orchestrator, evaluator, control)
        )
        audio_tasks[publication.sid] = task
        task.add_done_callback(lambda _task: audio_tasks.pop(publication.sid, None))

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        logger.info("track unsubscribed kind=%s sid=%s participant=%s", track.kind, publication.sid, participant.identity)
        task = audio_tasks.pop(publication.sid, None)
        if task:
            task.cancel()

    @room.on("track_muted")
    def on_track_muted(participant: rtc.Participant, publication: rtc.TrackPublication) -> None:
        logger.info("track muted sid=%s participant=%s", publication.sid, participant.identity)
        if participant.identity != AGENT_IDENTITY:
            asyncio.create_task(publish_json(room, {"type": "audio.state", "state": "muted"}))

    @room.on("track_unmuted")
    def on_track_unmuted(participant: rtc.Participant, publication: rtc.TrackPublication) -> None:
        logger.info("track unmuted sid=%s participant=%s", publication.sid, participant.identity)
        if participant.identity != AGENT_IDENTITY:
            asyncio.create_task(publish_json(room, {"type": "audio.state", "state": "unmuted"}))

    @room.on("data_received")
    def on_data_received(packet: rtc.DataPacket) -> None:
        if packet.topic != "control":
            return
        try:
            event = json.loads(packet.data.decode("utf-8"))
        except Exception:
            logger.warning("invalid control packet")
            return

        event_type = event.get("type")
        logger.info("control event type=%s", event_type)
        if event_type == "start_session":
            if control.started and not control.ended:
                return
            messages.clear()
            training_config = training_config_from_event(event)
            orchestrator.configure(**training_config)
            control.started = True
            control.ended = False
            control.finishing = False
            asyncio.create_task(
                publish_json(
                    room,
                    {
                        "type": "session.configured",
                        "modeId": training_config["mode_id"],
                        "modeLabel": option_label("modes", training_config["mode_id"]),
                        "competencyId": training_config["competency_id"],
                        "competencyLabel": option_label("competencies", training_config["competency_id"]),
                        "strategyId": training_config["strategy_id"],
                        "strategyLabel": option_label("strategies", training_config["strategy_id"]),
                    },
                )
            )
            asyncio.create_task(publish_json(room, {"type": "assistant.text.done", "text": orchestrator.opening_question}))
        elif event_type == "end_turn":
            control.force_finalize.set()
        elif event_type == "assistant_speaking":
            control.assistant_speaking = True
        elif event_type == "assistant_done":
            control.assistant_speaking = False
        elif event_type == "end_session":
            if control.finishing:
                return
            control.ended = True
            control.started = False
            control.finishing = True
            control.force_finalize.set()
            asyncio.create_task(finish_interview(room, orchestrator, evaluator, llm_provider, control))

    logger.info("connecting agent to room=%s url=%s", ROOM_NAME, LIVEKIT_URL)
    await room.connect(LIVEKIT_URL, create_agent_token())
    logger.info("agent connected to room=%s", ROOM_NAME)

    await publish_json(room, {"type": "assistant.state", "state": "connected"})
    await publish_json(room, {"type": "session.ready", "text": "AI 面试官已准备好。点击开始会话后，我会先问第一题。"})

    try:
        while room.isconnected():
            await asyncio.sleep(1)
    finally:
        for task in audio_tasks.values():
            task.cancel()
        await room.disconnect()


async def process_candidate_audio(
    room: rtc.Room,
    track: rtc.Track,
    publication: rtc.RemoteTrackPublication,
    messages: list[ConversationMessage],
    llm_provider: DeepSeekStreamingTextProvider,
    orchestrator: InterviewOrchestrator,
    evaluator: InterviewEvaluator,
    control: ConversationControl,
) -> None:
    logger.info("started candidate audio processor sid=%s", publication.sid)
    asr = FunAsrStreamingProvider()
    turn_controller = TurnController()
    completion_judge = TurnCompletionJudge()
    voice_gate = AdaptiveVoiceGate()
    audio_stream = rtc.AudioStream.from_track(track=track, sample_rate=16000, num_channels=1)
    active = False
    finalizing = False
    last_voice_notice_at = 0.0
    last_voice_seen_at = 0.0

    async for audio_event in audio_stream:
        if control.ended or not control.started or control.assistant_speaking:
            if active:
                asr.reset()
                turn_controller.reset_turn()
                active = False
                finalizing = False
                await publish_json(room, {"type": "transcript.cancelled", "reason": "session_paused"})
            control.force_finalize.clear()
            continue

        forced_finalize = control.force_finalize.is_set()
        if forced_finalize:
            control.force_finalize.clear()

        if publication.muted and not forced_finalize:
            if active:
                logger.info("candidate muted mic; discard current utterance sid=%s", publication.sid)
                asr.reset()
                turn_controller.reset_turn()
                active = False
                finalizing = False
                await publish_json(room, {"type": "transcript.cancelled", "reason": "mic_muted"})
            continue

        pcm_bytes = bytes(audio_event.frame.data)
        loop_time = asyncio.get_running_loop().time()
        rms = pcm_rms(pcm_bytes)
        has_voice, voice_threshold = voice_gate.classify(rms)

        if has_voice:
            active = True
            turn_controller.observe_audio(has_voice=True)
            last_voice_seen_at = loop_time
            if loop_time - last_voice_notice_at >= 1.0:
                last_voice_notice_at = loop_time
                logger.info("voice detected rms=%.4f threshold=%.4f sid=%s", rms, voice_threshold, publication.sid)
                await publish_json(
                    room,
                    {
                        "type": "audio.state",
                        "state": "voice",
                        "rms": round(rms, 4),
                        "threshold": round(voice_threshold, 4),
                        "noiseFloor": round(voice_gate.noise_floor, 4),
                    },
                )

        should_feed_asr = active and (has_voice or loop_time - last_voice_seen_at <= 0.35)
        if should_feed_asr:
            for update in await asr.push_audio(pcm_bytes):
                logger.info("partial transcript=%s", update.text)
                turn_controller.observe_transcript(update.text)
                await publish_json(room, {"type": "transcript.partial", "text": update.text})

        turn_action = TurnAction.NONE
        turn_reason = ""
        if forced_finalize:
            turn_action = TurnAction.END
            turn_reason = "manual fallback"
        elif active:
            action = await turn_controller.next_action(judge=completion_judge, messages=messages)
            turn_action = action.action
            turn_reason = action.reason
            if action.action is TurnAction.WAITING:
                await publish_json(room, {"type": "turn.waiting", "waitMs": action.wait_ms, "reason": action.reason})
            elif action.action is TurnAction.HINT:
                await publish_json(
                    room,
                    {"type": "turn.hint", "text": action.hint_text, "waitMs": action.wait_ms, "reason": action.reason},
                )

        if not finalizing and turn_action is TurnAction.END:
            finalizing = True
            final_update = await asr.finish_utterance()
            active = False
            finalizing = False
            turn_controller.reset_turn()
            if not final_update.text.strip():
                logger.info("final transcript empty")
                await publish_json(room, {"type": "transcript.empty"})
                continue
            logger.info("final transcript=%s", final_update.text)
            await publish_json(room, {"type": "transcript.final", "text": final_update.text, "reason": turn_reason})
            messages.append(ConversationMessage("user", final_update.text))
            orchestrator.record_candidate_answer(final_update.text)
            if orchestrator.should_finish:
                control.started = False
                control.ended = True
                if not control.finishing:
                    control.finishing = True
                    await finish_interview(room, orchestrator, evaluator, llm_provider, control)
            else:
                await stream_assistant_reply(room, messages, llm_provider, orchestrator)


async def stream_assistant_reply(
    room: rtc.Room,
    messages: list[ConversationMessage],
    llm_provider: DeepSeekStreamingTextProvider,
    orchestrator: InterviewOrchestrator,
) -> None:
    assistant_text = ""
    await publish_json(room, {"type": "assistant.state", "state": "thinking"})
    try:
        system_prompt = orchestrator.build_followup_prompt()
        async for chunk in llm_provider.stream_reply(messages, system_prompt=system_prompt):
            assistant_text += chunk
            await publish_json(room, {"type": "assistant.text.delta", "text": chunk})
    except Exception as error:
        logger.exception("DeepSeek reply failed")
        assistant_text = f"我调用 DeepSeek 时出错了：{error}"

    assistant_text = assistant_text.strip() or "你可以再补充一个更具体的项目细节吗？"
    messages.append(ConversationMessage("assistant", assistant_text))
    orchestrator.record_assistant_question(assistant_text)
    await publish_json(room, {"type": "assistant.text.done", "text": assistant_text})


async def finish_interview(
    room: rtc.Room,
    orchestrator: InterviewOrchestrator,
    evaluator: InterviewEvaluator,
    llm_provider: DeepSeekStreamingTextProvider,
    control: ConversationControl | None = None,
) -> None:
    try:
        await publish_json(room, {"type": "interview.evaluating"})
        try:
            report = await evaluator.evaluate(orchestrator=orchestrator, llm_provider=llm_provider)
        except Exception as error:
            logger.exception("interview evaluation failed")
            report = {
                "report_quality": "fallback",
                "summary": f"评分生成失败：{error}",
                "turn_count": orchestrator.state.candidate_turn_count,
                "coverage_ratio": round(orchestrator.coverage_ratio(), 2),
                "ability_model": {},
                "dimensions": [],
                "evidence_gaps": ["评分链路异常，需要查看后端日志"],
                "main_weakness": "当前不是候选人表现问题，而是评分链路异常。",
                "training_plan": {
                    "theme": "评分链路排查",
                    "goal": "确认 DeepSeek 与 JSON 评分输出是否正常。",
                    "tasks": [
                        {
                            "name": "重新生成评分",
                            "exercise": "重新完成一轮短面试后查看调试台和后端日志。",
                            "method": "先用 1-2 轮短回答测试评分事件是否返回。",
                            "success_criteria": "前端收到 interview.report，且 report_quality 不再是 fallback。",
                        }
                    ],
                    "duration_minutes": 5,
                },
            }
        await publish_json(room, {"type": "interview.report", "report": report})
        await publish_json(room, {"type": "session.ended", "text": "本轮面试已结束，评分和训练建议已生成。"})
    finally:
        if control:
            control.finishing = False


if __name__ == "__main__":
    asyncio.run(main())
