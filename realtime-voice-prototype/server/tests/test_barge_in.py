from app.session.barge_in import AssistantBargeInGate
from app.session.voice_activity import VoiceActivityFrame


def frame(
    *,
    has_voice: bool = True,
    rms: float = 0.04,
    duration_ms: int = 200,
    threshold: float = 0.018,
    noise_floor: float = 0.006,
) -> VoiceActivityFrame:
    return VoiceActivityFrame(
        has_voice=has_voice,
        rms=rms,
        duration_ms=duration_ms,
        threshold=threshold,
        noise_floor=noise_floor,
    )


def test_barge_in_requires_sustained_strong_voice() -> None:
    gate = AssistantBargeInGate()

    assert gate.observe(frame(duration_ms=200)) is False
    assert gate.observe(frame(duration_ms=200)) is False
    assert gate.observe(frame(duration_ms=200)) is True


def test_barge_in_ignores_weak_background_voice() -> None:
    gate = AssistantBargeInGate()

    weak_background = frame(rms=0.02, duration_ms=1000)

    assert gate.observe(weak_background) is False


def test_barge_in_identifies_strong_voice_frames() -> None:
    gate = AssistantBargeInGate()

    assert gate.is_strong_voice(frame(rms=0.04)) is True
    assert gate.is_strong_voice(frame(rms=0.02)) is False


def test_barge_in_resets_after_silence() -> None:
    gate = AssistantBargeInGate()

    assert gate.observe(frame(duration_ms=400)) is False
    assert gate.observe(frame(has_voice=False, rms=0.0, duration_ms=200)) is False
    assert gate.observe(frame(duration_ms=200)) is False
