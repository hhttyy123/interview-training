import asyncio
from contextlib import suppress
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.interview.prompt_builder import build_interviewer_prompt
from app.providers.asr.funasr_streaming import FunAsrStreamingProvider
from app.providers.llm.selected import create_streaming_text_provider
from app.protocol.client_events import ClientEvent, parse_client_event
from app.protocol.server_events import (
    assistant_cancelled,
    assistant_text_delta,
    assistant_text_done,
    session_ended,
    session_error,
    session_ready,
    transcript_final,
    transcript_partial,
    turn_state,
)
from app.providers.llm.turn_completion_judge import DeepSeekTurnCompletionJudge
from app.session.barge_in import AssistantBargeInGate
from app.session.manager import VoiceSessionManager
from app.session.turn_controller import TurnAction, TurnController, TurnControllerAction, TurnDecisionTrace
from app.session.voice_activity import VoiceActivityDetector


router = APIRouter()
logger = logging.getLogger(__name__)
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}
MANUAL_END_LOCK_SECONDS = 1.5
NO_TRANSCRIPT_REPLY = "\u6211\u6ca1\u6709\u542c\u6e05\u8fd9\u4e00\u8f6e\u7684\u56de\u7b54\uff0c\u53ef\u4ee5\u518d\u8bf4\u4e00\u904d\u5417\uff1f"
EMPTY_ASSISTANT_REPLY = "\u6211\u521a\u624d\u6ca1\u6709\u751f\u6210\u6709\u6548\u8ffd\u95ee\uff0c\u53ef\u4ee5\u518d\u8865\u5145\u4e00\u4e2a\u5177\u4f53\u4f8b\u5b50\u5417\uff1f"
NON_ANSWER_TRANSCRIPTS = {
    "\u55ef",
    "\u55ef\u55ef",
    "\u554a",
    "\u5443",
    "\u989d",
    "\u54e6",
    "\u597d",
}


def _training_value(payload: dict[str, object], key: str, default: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return default


def _trace_payload(trace: TurnDecisionTrace) -> dict[str, object]:
    return {
        "active": trace.active,
        "action": trace.action,
        "pause_ms": trace.pause_ms,
        "stable_ms": trace.stable_ms,
        "transcript_length": trace.transcript_length,
        "judge_status": trace.judge_status,
        "judge_confidence": trace.judge_confidence,
        "judge_latency_ms": trace.judge_latency_ms,
        "wait_ms": trace.wait_ms,
        "reason": trace.reason,
    }


def _normalized_transcript(text: str) -> str:
    return "".join(character for character in text.strip().lower() if character.isalnum() or "\u4e00" <= character <= "\u9fff")


def _is_non_answer_transcript(text: str) -> bool:
    normalized = _normalized_transcript(text)
    return normalized in NON_ANSWER_TRANSCRIPTS


@router.websocket("/ws/voice")
async def voice_session(websocket: WebSocket) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    manager = VoiceSessionManager()
    asr = FunAsrStreamingProvider()
    text_provider = create_streaming_text_provider()
    turn_controller = TurnController()
    turn_judge = DeepSeekTurnCompletionJudge()
    voice_activity = VoiceActivityDetector()
    barge_in_gate = AssistantBargeInGate()
    send_lock = asyncio.Lock()
    assistant_task: asyncio.Task[None] | None = None
    turn_monitor_task: asyncio.Task[None] | None = None
    barge_in_audio_buffer: list[bytes] = []
    manual_end_lock_until = 0.0
    training_config = {
        "job_id": "product_manager",
        "mode_id": "standard",
        "competency_id": "requirement_analysis",
        "strategy_id": "evidence_probe",
    }

    async def send_json(payload: dict[str, object]) -> None:
        async with send_lock:
            await websocket.send_json(payload)

    async def cancel_assistant(reason: str, *, notify: bool = True) -> None:
        nonlocal assistant_task
        if assistant_task is None or assistant_task.done():
            assistant_task = None
            return
        assistant_task.cancel()
        with suppress(asyncio.CancelledError):
            await assistant_task
        assistant_task = None
        if notify:
            await send_json(assistant_cancelled(reason))

    async def cancel_turn_monitor() -> None:
        nonlocal turn_monitor_task
        if turn_monitor_task is None or turn_monitor_task.done():
            turn_monitor_task = None
            return
        turn_monitor_task.cancel()
        with suppress(asyncio.CancelledError):
            await turn_monitor_task
        turn_monitor_task = None

    async def stream_assistant_reply() -> None:
        assistant_text = ""
        prompt = build_interviewer_prompt(**training_config)
        try:
            async for chunk in text_provider.stream_reply(manager.messages(), system_prompt=prompt):
                assistant_text += chunk
                await send_json(assistant_text_delta(chunk))
        except asyncio.CancelledError:
            logger.info("Assistant response cancelled because the user started speaking.")
            raise
        except Exception as error:
            logger.exception("Assistant response failed.")
            await send_json(session_error(f"Assistant response failed: {error}"))
            return
        if not assistant_text:
            logger.warning("Assistant stream completed without text content.")
            assistant_text = EMPTY_ASSISTANT_REPLY
        manager.add_assistant_message(assistant_text)
        await send_json(assistant_text_done(assistant_text))

    async def finalize_current_turn(reason: str) -> None:
        nonlocal assistant_task
        if not manager.is_active():
            await send_json(session_error("Start a session before finalizing audio."))
            return
        try:
            update = await asr.finish_utterance()
        except Exception as error:
            await send_json(session_error(f"Speech recognition failed: {error}"))
            turn_controller.reset_turn()
            return
        turn_controller.reset_turn()
        await send_json(turn_state("processing", reason=reason))
        await send_json(transcript_final(update.text))
        if not update.text:
            logger.info("Skipping LLM response because final transcript is empty.")
            await send_json(assistant_text_done(NO_TRANSCRIPT_REPLY))
            return
        if _is_non_answer_transcript(update.text):
            logger.info("Ignoring non-answer transcript: %s", update.text)
            await send_json(turn_state("listening", reason="non-answer transcript ignored"))
            return
        manager.add_user_message(update.text)
        await cancel_assistant("\u65b0\u7684\u7528\u6237\u56de\u7b54\u5df2\u786e\u8ba4")
        barge_in_gate.reset()
        assistant_task = asyncio.create_task(stream_assistant_reply())

    async def handle_turn_action(action: TurnControllerAction) -> None:
        if action.trace is not None:
            if action.action is TurnAction.NONE:
                logger.debug("turn_decision=%s", _trace_payload(action.trace))
            else:
                logger.info("turn_decision=%s", _trace_payload(action.trace))
        if action.action is TurnAction.END:
            await finalize_current_turn(action.reason)
            return
        if action.action is TurnAction.WAITING:
            await send_json(
                turn_state(
                    "waiting_for_more",
                    wait_ms=action.wait_ms,
                    hint_after_ms=action.hint_after_ms,
                    hint_text=action.hint_text,
                    reason=action.reason,
                )
            )
            return
        if action.action is TurnAction.HINT:
            await send_json(
                turn_state(
                    "hint",
                    wait_ms=action.wait_ms,
                    hint_text=action.hint_text,
                    reason=action.reason,
                )
            )

    async def monitor_turns() -> None:
        while manager.is_active():
            await asyncio.sleep(0.25)
            action = await turn_controller.next_action(
                judge=turn_judge,
                messages=manager.messages(),
                mode_id=training_config["mode_id"],
                competency_id=training_config["competency_id"],
            )
            await handle_turn_action(action)

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"] is not None:
                if not manager.is_active():
                    await send_json(session_error("Start a session before sending audio."))
                    continue
                audio_bytes = message["bytes"]
                frame = voice_activity.inspect(audio_bytes)
                now = time.monotonic()
                assistant_is_streaming = assistant_task is not None and not assistant_task.done()
                if assistant_is_streaming:
                    if now < manual_end_lock_until:
                        barge_in_gate.reset()
                        barge_in_audio_buffer.clear()
                        continue
                    if barge_in_gate.is_strong_voice(frame):
                        barge_in_audio_buffer.append(audio_bytes)
                    else:
                        barge_in_audio_buffer.clear()
                    if not barge_in_gate.observe(frame):
                        continue
                    await cancel_assistant("\u7528\u6237\u6253\u65ad\u4e86 AI \u56de\u590d")
                    asr.reset()
                    turn_controller.reset_turn()
                    await send_json(turn_state("listening", reason="\u7528\u6237\u6253\u65ad\u4e86 AI \u56de\u590d"))
                    audio_chunks = list(barge_in_audio_buffer)
                    barge_in_audio_buffer.clear()
                else:
                    barge_in_gate.reset()
                    barge_in_audio_buffer.clear()
                    audio_chunks = [audio_bytes]

                if frame.is_near_voice():
                    turn_controller.observe_audio(has_voice=True, now=now)
                else:
                    turn_controller.observe_audio(has_voice=False, now=now)
                if not turn_controller.active:
                    continue
                try:
                    updates = []
                    for chunk in audio_chunks:
                        updates.extend(await asr.push_audio(chunk))
                except Exception as error:
                    await send_json(session_error(f"Speech recognition failed: {error}"))
                    continue
                for update in updates:
                    turn_controller.observe_transcript(update.text)
                    await send_json(transcript_partial(update.text))
                continue
            if message.get("type") == "websocket.disconnect":
                break
            try:
                payload = json.loads(message.get("text", "{}"))
            except (json.JSONDecodeError, TypeError):
                await send_json(session_error("Malformed session event JSON."))
                continue
            if not isinstance(payload, dict):
                await send_json(session_error("Session event must be a JSON object."))
                continue
            event = parse_client_event(payload)
            if event is None:
                await send_json(session_error("Unsupported session event."))
                continue
            if event is ClientEvent.START:
                await cancel_assistant("\u4f1a\u8bdd\u5df2\u91cd\u65b0\u5f00\u59cb")
                await cancel_turn_monitor()
                barge_in_gate.reset()
                manual_end_lock_until = 0.0
                training_config = {
                    "job_id": _training_value(payload, "jobId", "product_manager"),
                    "mode_id": _training_value(payload, "modeId", "standard"),
                    "competency_id": _training_value(payload, "competencyId", "requirement_analysis"),
                    "strategy_id": _training_value(payload, "strategyId", "evidence_probe"),
                }
                logger.info("Starting voice session with training_config=%s", training_config)
                session = manager.start()
                asr.reset()
                turn_controller.reset_turn()
                await send_json(session_ready(session.session_id))
                turn_monitor_task = asyncio.create_task(monitor_turns())
                continue
            if event is ClientEvent.AUDIO_BEGIN:
                if not manager.is_active():
                    await send_json(session_error("Start a session before using the microphone."))
                    continue
                asr.reset()
                barge_in_gate.reset()
                turn_controller.reset_turn()
                await send_json(turn_state("listening"))
                continue
            if event is ClientEvent.AUDIO_END:
                manual_end_lock_until = time.monotonic() + MANUAL_END_LOCK_SECONDS
                barge_in_gate.reset()
                await finalize_current_turn("manual turn end")
                continue
            if event is ClientEvent.STOP:
                await cancel_assistant("\u4f1a\u8bdd\u5df2\u505c\u6b62")
                await cancel_turn_monitor()
                barge_in_gate.reset()
                manual_end_lock_until = 0.0
                ended_session_id = manager.stop()
                if ended_session_id is None:
                    await send_json(session_error("No active session to stop."))
                    continue
                await send_json(session_ended(ended_session_id))
    except WebSocketDisconnect:
        pass
    finally:
        await cancel_assistant("socket disconnected", notify=False)
        await cancel_turn_monitor()
        asr.reset()
        turn_controller.reset_turn()
        manager.stop()
