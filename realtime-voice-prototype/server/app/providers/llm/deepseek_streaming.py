import json
import os
from collections.abc import AsyncIterator, Sequence

import httpx

from app.session.state import ConversationMessage


DEFAULT_SYSTEM_PROMPT = (
    "You are a real-time voice interview training assistant. "
    "Keep replies short, conversational, and suitable for later text-to-speech playback. "
    "Ask only one follow-up question at a time, based on the user's latest answer."
)


class DeepSeekStreamingTextProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.system_prompt = system_prompt

    async def stream_reply(
        self,
        messages: Sequence[ConversationMessage],
        *,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set.")

        payload = self._chat_payload(messages, system_prompt=system_prompt)
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

    def _messages_payload(
        self,
        messages: Sequence[ConversationMessage],
        *,
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        payload = [{"role": "system", "content": system_prompt or self.system_prompt}]
        for message in messages[-10:]:
            if message.role not in {"user", "assistant"}:
                continue
            payload.append({"role": message.role, "content": message.text})
        return payload

    def _chat_payload(
        self,
        messages: Sequence[ConversationMessage],
        *,
        system_prompt: str | None = None,
    ) -> dict[str, object]:
        return {
            "model": self.model,
            "messages": self._messages_payload(messages, system_prompt=system_prompt),
            "stream": True,
            "thinking": {"type": "disabled"},
            "temperature": 0.4,
        }

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
        delta = choices[0].get("delta", {})
        content = delta.get("content")
        if not isinstance(content, str):
            return ""
        return content
