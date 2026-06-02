from app.session.voice_activity import VoiceActivityFrame


def test_near_voice_requires_more_than_basic_vad_hit() -> None:
    background_voice = VoiceActivityFrame(
        has_voice=True,
        rms=0.0185,
        duration_ms=200,
        threshold=0.018,
        noise_floor=0.006,
    )

    assert background_voice.is_near_voice() is False


def test_near_voice_accepts_clear_close_speech() -> None:
    close_speech = VoiceActivityFrame(
        has_voice=True,
        rms=0.04,
        duration_ms=200,
        threshold=0.018,
        noise_floor=0.006,
    )

    assert close_speech.is_near_voice() is True
