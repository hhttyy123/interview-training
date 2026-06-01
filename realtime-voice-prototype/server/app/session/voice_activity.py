import math

import numpy as np


class VoiceActivityDetector:
    """Lightweight speech activity gate for PCM16 browser audio."""

    min_rms = 0.012
    noise_multiplier = 3.0

    def __init__(self) -> None:
        self.noise_floor = 0.006

    def inspect(self, pcm_bytes: bytes) -> tuple[bool, float, int]:
        if not pcm_bytes:
            return False, 0.0, 0

        samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
        if len(samples) == 0:
            return False, 0.0, 0

        rms = float(math.sqrt(float(np.mean(np.square(samples)))))
        threshold = max(self.min_rms, self.noise_floor * self.noise_multiplier)
        has_voice = rms >= threshold
        if not has_voice:
            self.noise_floor = (self.noise_floor * 0.95) + (rms * 0.05)
        duration_ms = int((len(samples) / 16000) * 1000)
        return has_voice, rms, duration_ms
