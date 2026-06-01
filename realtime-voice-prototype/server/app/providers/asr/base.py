from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptUpdate:
    text: str
    final: bool


class StreamingAsr(Protocol):
    async def push_audio(self, pcm_bytes: bytes) -> list[TranscriptUpdate]: ...

    async def finish_utterance(self) -> TranscriptUpdate: ...

    def reset(self) -> None: ...
