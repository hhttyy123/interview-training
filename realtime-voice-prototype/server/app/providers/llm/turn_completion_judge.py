import json
import os

import httpx

from app.session.turn_completion import (
    CompletionStatus,
    TurnCompletionDecision,
    TurnCompletionJudge,
    TurnCompletionRequest,
    rule_based_completion,
)


SYSTEM_PROMPT = """
You judge whether a job-interview candidate has finished the current speaking turn.
Return only JSON. Do not ask a follow-up question.

Fields:
- completion: complete, incomplete, or uncertain
- confidence: number from 0 to 1
- suggested_wait_ms: integer wait time before ending the turn
- reason: short internal reason in English

Prefer incomplete when the candidate appears to be thinking, stops after a connector,
or has not given enough content for an interviewer to respond naturally.
""".strip()


class DeepSeekTurnCompletionJudge(TurnCompletionJudge):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")

    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        rule_decision = rule_based_completion(request)
        if rule_decision.completion is not CompletionStatus.UNCERTAIN:
            return rule_decision
        if not self.api_key:
            return rule_decision

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self._user_prompt(request)},
            ],
            "stream": False,
            "temperature": 0,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        except httpx.HTTPError:
            return rule_decision
        if response.status_code >= 400:
            return rule_decision
        return self._parse_response(response.text, fallback=rule_decision)

    def _user_prompt(self, request: TurnCompletionRequest) -> str:
        context = [
            {"role": message.role, "text": message.text}
            for message in request.messages[-6:]
            if message.role in {"user", "assistant"}
        ]
        return json.dumps(
            {
                "transcript": request.transcript,
                "pause_ms": request.pause_ms,
                "utterance_duration_ms": request.utterance_duration_ms,
                "mode_id": request.mode_id,
                "competency_id": request.competency_id,
                "recent_context": context,
            },
            ensure_ascii=False,
        )

    def _parse_response(self, body: str, *, fallback: TurnCompletionDecision) -> TurnCompletionDecision:
        try:
            payload = json.loads(body)
            content = payload["choices"][0]["message"]["content"]
            decision = json.loads(content)
            completion = CompletionStatus(str(decision.get("completion", "uncertain")))
            confidence = max(0.0, min(1.0, float(decision.get("confidence", 0.5))))
            suggested_wait_ms = max(0, int(decision.get("suggested_wait_ms", fallback.suggested_wait_ms)))
            reason = str(decision.get("reason", "llm judge"))
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return fallback
        return TurnCompletionDecision(completion, confidence, suggested_wait_ms, reason)
