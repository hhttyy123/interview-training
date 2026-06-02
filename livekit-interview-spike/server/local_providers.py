import asyncio
import json
import math
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from threading import Lock

import httpx
import numpy as np


@dataclass(frozen=True)
class TranscriptUpdate:
    text: str
    final: bool


_shared_funasr_model: object | None = None
_shared_funasr_lock = Lock()


def load_shared_funasr_model() -> object:
    global _shared_funasr_model
    if _shared_funasr_model is None:
        with _shared_funasr_lock:
            if _shared_funasr_model is None:
                from funasr import AutoModel

                _shared_funasr_model = AutoModel(model="paraformer-zh-streaming", disable_update=True)
    return _shared_funasr_model


async def preload_shared_funasr_model() -> None:
    await asyncio.to_thread(load_shared_funasr_model)


class FunAsrStreamingProvider:
    chunk_size = [0, 10, 5]
    chunk_samples = 9600
    first_chunk_samples = 4800
    encoder_chunk_look_back = 4
    decoder_chunk_look_back = 1

    def __init__(self) -> None:
        self._model: object | None = None
        self._cache: dict = {}
        self._pending = np.array([], dtype=np.float32)
        self._transcript = ""
        self._has_transcribed_once = False

    async def push_audio(self, pcm_bytes: bytes) -> list[TranscriptUpdate]:
        samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
        self._pending = np.concatenate((self._pending, samples))
        updates: list[TranscriptUpdate] = []
        while len(self._pending) >= self._next_chunk_samples():
            chunk_samples = self._next_chunk_samples()
            chunk = self._pending[:chunk_samples]
            self._pending = self._pending[chunk_samples:]
            text = await asyncio.to_thread(self._transcribe, chunk, False)
            self._has_transcribed_once = True
            if text:
                self._transcript += text
                updates.append(TranscriptUpdate(self._transcript, False))
        return updates

    async def finish_utterance(self) -> TranscriptUpdate:
        text = ""
        if len(self._pending):
            text = await asyncio.to_thread(self._transcribe, self._pending, True)
        elif self._model is not None:
            text = await asyncio.to_thread(self._transcribe, np.array([], dtype=np.float32), True)
        if text:
            self._transcript += text
        update = TranscriptUpdate(self._transcript, True)
        self.reset()
        return update

    def reset(self) -> None:
        self._cache = {}
        self._pending = np.array([], dtype=np.float32)
        self._transcript = ""
        self._has_transcribed_once = False

    def _next_chunk_samples(self) -> int:
        return self.chunk_samples if self._has_transcribed_once else self.first_chunk_samples

    def _transcribe(self, chunk: np.ndarray, is_final: bool) -> str:
        if self._model is None:
            self._model = load_shared_funasr_model()
        result = self._model.generate(
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


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    text: str


class DeepSeekStreamingTextProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")

    async def stream_reply(
        self,
        messages: list[ConversationMessage],
        *,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            yield "我还没有配置 DeepSeek API Key。请先在 .env 里填写 DEEPSEEK_API_KEY。"
            return

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}]
            + [{"role": item.role, "content": item.text} for item in messages[-10:]],
            "stream": True,
            "temperature": 0.4,
            "thinking": {"type": "disabled"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise RuntimeError(
                        f"DeepSeek request failed with {response.status_code}: {detail.decode(errors='ignore')}"
                    )
                async for line in response.aiter_lines():
                    chunk = self._parse_sse_line(line)
                    if chunk:
                        yield chunk

    def _parse_sse_line(self, line: str) -> str:
        line = line.strip()
        if not line.startswith("data:"):
            return ""
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return ""
        payload = json.loads(data)
        choices = payload.get("choices", [])
        if not choices:
            return ""
        content = choices[0].get("delta", {}).get("content")
        return content if isinstance(content, str) else ""


async def synthesize_edge_tts(text: str, *, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+18%") -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)


def pcm_rms(pcm_bytes: bytes) -> float:
    if not pcm_bytes:
        return 0.0
    samples = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) / 32768.0
    if len(samples) == 0:
        return 0.0
    return float(math.sqrt(float(np.mean(np.square(samples)))))
