import asyncio
from collections.abc import Callable
from threading import Lock

import numpy as np

from app.providers.asr.base import TranscriptUpdate


ModelFactory = Callable[[], object]

_shared_model: object | None = None
_shared_model_lock = Lock()


def load_shared_funasr_model() -> object:
    global _shared_model
    if _shared_model is None:
        with _shared_model_lock:
            if _shared_model is None:
                from funasr import AutoModel

                _shared_model = AutoModel(model="paraformer-zh-streaming", disable_update=True)
    return _shared_model


async def preload_shared_funasr_model() -> None:
    await asyncio.to_thread(load_shared_funasr_model)


class FunAsrStreamingProvider:
    """Buffers browser PCM into the chunk profile expected by Paraformer streaming."""

    chunk_size = [0, 10, 5]
    chunk_samples = 9600  # 600 ms of 16 kHz PCM, following FunASR's example.
    encoder_chunk_look_back = 4
    decoder_chunk_look_back = 1

    def __init__(self, model_factory: ModelFactory | None = None) -> None:
        self._model_factory = model_factory or self._default_model_factory
        self._model: object | None = None
        self._cache: dict = {}
        self._pending = np.array([], dtype=np.float32)
        self._transcript = ""

    async def push_audio(self, pcm_bytes: bytes) -> list[TranscriptUpdate]:
        samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
        self._pending = np.concatenate((self._pending, samples))
        updates: list[TranscriptUpdate] = []
        while len(self._pending) >= self.chunk_samples:
            chunk = self._pending[: self.chunk_samples]
            self._pending = self._pending[self.chunk_samples :]
            text = await asyncio.to_thread(self._transcribe, chunk, False)
            if text:
                self._transcript += text
                updates.append(TranscriptUpdate(text=self._transcript, final=False))
        return updates

    async def finish_utterance(self) -> TranscriptUpdate:
        text = ""
        if len(self._pending):
            text = await asyncio.to_thread(self._transcribe, self._pending, True)
        elif self._model is not None:
            text = await asyncio.to_thread(self._transcribe, np.array([], dtype=np.float32), True)
        if text:
            self._transcript += text
        update = TranscriptUpdate(text=self._transcript, final=True)
        self.reset()
        return update

    def reset(self) -> None:
        self._cache = {}
        self._pending = np.array([], dtype=np.float32)
        self._transcript = ""

    def _transcribe(self, chunk: np.ndarray, is_final: bool) -> str:
        model = self._get_model()
        result = model.generate(
            input=chunk,
            cache=self._cache,
            is_final=is_final,
            chunk_size=self.chunk_size,
            encoder_chunk_look_back=self.encoder_chunk_look_back,
            decoder_chunk_look_back=self.decoder_chunk_look_back,
        )
        if not result:
            return ""
        return str(result[0].get("text", ""))

    def _get_model(self) -> object:
        if self._model is None:
            self._model = self._model_factory()
        return self._model

    @staticmethod
    def _default_model_factory() -> object:
        return load_shared_funasr_model()
