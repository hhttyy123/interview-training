from dataclasses import dataclass
from enum import Enum

from app.session.state import ConversationMessage


class CompletionStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class TurnCompletionRequest:
    transcript: str
    pause_ms: int
    utterance_duration_ms: int
    messages: list[ConversationMessage]
    mode_id: str
    competency_id: str


@dataclass(frozen=True)
class TurnCompletionDecision:
    completion: CompletionStatus
    confidence: float
    suggested_wait_ms: int
    reason: str


class TurnCompletionJudge:
    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        return rule_based_completion(request)


THINKING_PHRASES = (
    "\u6211\u60f3\u4e00\u4e0b",
    "\u6211\u60f3\u60f3",
    "\u7b49\u4e00\u4e0b",
    "\u7a0d\u7b49",
)

OPEN_ENDINGS = (
    "\u7136\u540e",
    "\u56e0\u4e3a",
    "\u6bd4\u5982",
    "\u6211\u89c9\u5f97",
    "\u8fd9\u4e2a",
    "\u4e3b\u8981\u662f",
    "\u6240\u4ee5",
    "\u800c\u4e14",
)


def rule_based_completion(request: TurnCompletionRequest) -> TurnCompletionDecision:
    text = request.transcript.strip()
    if not text:
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.9, 18000, "empty transcript")

    if any(phrase in text[-12:] for phrase in THINKING_PHRASES):
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.86, 20000, "thinking phrase")

    if any(text.endswith(ending) for ending in OPEN_ENDINGS):
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.82, 18000, "open-ended phrase")

    if len(text) < 12:
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.68, 4500, "short answer")

    if text[-1:] in ".!?;:\u3002\uff01\uff1f\uff1b" and len(text) >= 24:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.82, 0, "sentence-ending punctuation")

    if len(text) >= 80 and request.pause_ms >= 1200:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.78, 0, "long answer with pause")

    if len(text) >= 36 and request.pause_ms >= 1200:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.76, 0, "answer-length pause")

    return TurnCompletionDecision(CompletionStatus.UNCERTAIN, 0.5, 5500, "ambiguous pause")
