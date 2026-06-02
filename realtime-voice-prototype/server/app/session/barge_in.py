from app.session.voice_activity import VoiceActivityFrame


class AssistantBargeInGate:
    """Confirms intentional user interruption while the assistant is streaming."""

    min_voice_ms = 600
    threshold_multiplier = 1.35
    noise_floor_multiplier = 5.0
    min_interrupt_rms = 0.025

    def __init__(self) -> None:
        self.strong_voice_ms = 0

    def reset(self) -> None:
        self.strong_voice_ms = 0

    def is_strong_voice(self, frame: VoiceActivityFrame) -> bool:
        if not frame.has_voice:
            return False

        return frame.rms >= max(
            self.min_interrupt_rms,
            frame.threshold * self.threshold_multiplier,
            frame.noise_floor * self.noise_floor_multiplier,
        )

    def observe(self, frame: VoiceActivityFrame) -> bool:
        if not self.is_strong_voice(frame):
            self.reset()
            return False

        self.strong_voice_ms += frame.duration_ms
        return self.strong_voice_ms >= self.min_voice_ms
