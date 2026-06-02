import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VoiceActivityFrame:
    has_voice: bool
    rms: float
    duration_ms: int
    threshold: float
    noise_floor: float

    def is_near_voice(self) -> bool:
        if not self.has_voice:
            return False
        near_voice_threshold = max(0.016, self.threshold * 1.1, self.noise_floor * 3.6)
        return self.rms >= near_voice_threshold


class VoiceActivityDetector:
    """Lightweight speech activity gate for PCM16 browser audio."""

    min_rms = 0.012
    noise_multiplier = 3.0

    def __init__(self) -> None:
        self.noise_floor = 0.006

    def inspect(self, pcm_bytes: bytes) -> VoiceActivityFrame:
        threshold = max(self.min_rms, self.noise_floor * self.noise_multiplier)
        if not pcm_bytes:
            return VoiceActivityFrame(False, 0.0, 0, threshold, self.noise_floor)

        samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
        if len(samples) == 0:
            return VoiceActivityFrame(False, 0.0, 0, threshold, self.noise_floor)

        rms = float(math.sqrt(float(np.mean(np.square(samples)))))
        noise_floor = self.noise_floor
        threshold = max(self.min_rms, noise_floor * self.noise_multiplier)
        has_voice = rms >= threshold
        if not has_voice:
            self.noise_floor = (self.noise_floor * 0.95) + (rms * 0.05)
        duration_ms = int((len(samples) / 16000) * 1000)
        return VoiceActivityFrame(has_voice, rms, duration_ms, threshold, noise_floor)
