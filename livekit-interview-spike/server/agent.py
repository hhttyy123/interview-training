import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import api, rtc

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

SYSTEM_PROMPT = """
你是一个面向应届生的公司岗位级 AI 面试训练教练。
当前测试场景是产品经理岗位真实语音模拟面试。
全程使用中文。每次只问一个问题。
追问必须基于候选人刚才的回答。
如果回答缺少背景、行动、结果或量化证据，就继续追问。
如果候选人卡顿或表示正在思考，给他时间，不要催促。
回复要简短自然，适合语音播报，不要输出复杂格式。
""".strip()

OPENING_QUESTION = "你好，我们开始一轮产品经理模拟面试。请先用一分钟介绍一个最能代表你产品能力的项目。"


class AdaptiveVoiceGate:
    min_voice_threshold = 0.012
    voice_margin = 0.010
    speech_threshold_ratio = 2.6
    noise_smoothing = 0.985

    def __init__(self) -> None:
        self.noise_floor = 0.006

    def classify(self, rms: float) -> tuple[bool, float]:
        threshold = max(self.min_voice_threshold, self.noise_floor * self.speech_threshold_ratio, self.noise_floor + self.voice_margin)
        has_voice = rms >= threshold
        if not has_voice:
            self.noise_floor = self.noise_floor * self.noise_smoothing + rms * (1 - self.noise_smoothing)
        return has_voice, threshold


class ConversationControl:
    def __init__(self) -> None:
        self.started = False
        self.ended = False
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


async def main() -> None:
    logger.info("preloading FunASR model")
    await preload_shared_funasr_model()
    logger.info("FunASR model ready")

    room = rtc.Room()
    messages: list[ConversationMessage] = []
    llm_provider = DeepSeekStreamingTextProvider()
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

        task = asyncio.create_task(process_candidate_audio(room, track, publication, messages, llm_provider, control))
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
            control.started = True
            control.ended = False
            asyncio.create_task(publish_json(room, {"type": "assistant.text.done", "text": OPENING_QUESTION}))
        elif event_type == "end_turn":
            control.force_finalize.set()
        elif event_type == "assistant_speaking":
            control.assistant_speaking = True
        elif event_type == "assistant_done":
            control.assistant_speaking = False
        elif event_type == "end_session":
            control.ended = True
            control.started = False
            control.force_finalize.set()
            asyncio.create_task(publish_json(room, {"type": "session.ended", "text": "本轮面试已结束。"}))

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
    voice_threshold = 0.012

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
                await publish_json(
                    room,
                    {
                        "type": "turn.waiting",
                        "waitMs": action.wait_ms,
                        "reason": action.reason,
                    },
                )
            elif action.action is TurnAction.HINT:
                await publish_json(
                    room,
                    {
                        "type": "turn.hint",
                        "text": action.hint_text,
                        "waitMs": action.wait_ms,
                        "reason": action.reason,
                    },
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
            await stream_assistant_reply(room, messages, llm_provider)


async def stream_assistant_reply(
    room: rtc.Room,
    messages: list[ConversationMessage],
    llm_provider: DeepSeekStreamingTextProvider,
) -> None:
    assistant_text = ""
    await publish_json(room, {"type": "assistant.state", "state": "thinking"})
    try:
        async for chunk in llm_provider.stream_reply(messages, system_prompt=SYSTEM_PROMPT):
            assistant_text += chunk
            await publish_json(room, {"type": "assistant.text.delta", "text": chunk})
    except Exception as error:
        logger.exception("DeepSeek reply failed")
        assistant_text = f"我调用 DeepSeek 时出错了：{error}"

    assistant_text = assistant_text.strip() or "我刚才没有生成有效追问。你可以再补充一个具体例子吗？"
    messages.append(ConversationMessage("assistant", assistant_text))
    await publish_json(room, {"type": "assistant.text.done", "text": assistant_text})


if __name__ == "__main__":
    asyncio.run(main())
