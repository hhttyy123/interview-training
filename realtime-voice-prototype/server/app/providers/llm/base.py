from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from app.session.state import ConversationMessage


class StreamingTextProvider(Protocol):
    def stream_reply(
        self,
        messages: Sequence[ConversationMessage],
        *,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]: ...
