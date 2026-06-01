def session_ready(session_id: str) -> dict[str, str]:
    return {"type": "session.ready", "session_id": session_id}


def session_ended(session_id: str) -> dict[str, str]:
    return {"type": "session.ended", "session_id": session_id}


def session_error(message: str) -> dict[str, str]:
    return {"type": "session.error", "message": message}


def transcript_partial(text: str) -> dict[str, str]:
    return {"type": "transcript.partial", "text": text}


def transcript_final(text: str) -> dict[str, str]:
    return {"type": "transcript.final", "text": text}


def assistant_text_delta(text: str) -> dict[str, str]:
    return {"type": "assistant.text.delta", "text": text}


def assistant_text_done(text: str) -> dict[str, str]:
    return {"type": "assistant.text.done", "text": text}


def assistant_cancelled(reason: str) -> dict[str, str]:
    return {"type": "assistant.cancelled", "reason": reason}


def turn_state(
    state: str,
    *,
    wait_ms: int = 0,
    hint_after_ms: int = 0,
    hint_text: str = "",
    reason: str = "",
) -> dict[str, str | int]:
    return {
        "type": "turn.state",
        "state": state,
        "wait_ms": wait_ms,
        "hint_after_ms": hint_after_ms,
        "hint_text": hint_text,
        "reason": reason,
    }
