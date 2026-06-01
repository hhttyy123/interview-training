from app.providers.llm.base import StreamingTextProvider
from app.providers.llm.deepseek_streaming import DeepSeekStreamingTextProvider


def create_streaming_text_provider() -> StreamingTextProvider:
    return DeepSeekStreamingTextProvider()
