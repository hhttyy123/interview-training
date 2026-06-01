import numpy as np
import pytest

from app.providers.asr.funasr_streaming import FunAsrStreamingProvider


class FakeModel:
    def generate(self, **kwargs) -> list[dict[str, str]]:
        if kwargs["is_final"]:
            return [{"text": "结束"}]
        return [{"text": "你好"}]


@pytest.mark.anyio
async def test_streaming_provider_returns_partial_and_final_transcript() -> None:
    provider = FunAsrStreamingProvider(model_factory=FakeModel)
    pcm = (np.zeros(provider.chunk_samples, dtype=np.int16)).tobytes()

    partial = await provider.push_audio(pcm)
    final = await provider.finish_utterance()

    assert partial[0].text == "你好"
    assert partial[0].final is False
    assert final.text == "你好结束"
    assert final.final is True
