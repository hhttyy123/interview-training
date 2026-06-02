from dataclasses import dataclass
from enum import Enum

from local_providers import ConversationMessage


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
    "我想一下",
    "我想想",
    "等一下",
    "稍等",
    "让我想",
    "我思考",
)

OPEN_ENDINGS = (
    "然后",
    "因为",
    "比如",
    "我觉得",
    "这个",
    "主要是",
    "所以",
    "而且",
    "但是",
    "另外",
)


def rule_based_completion(request: TurnCompletionRequest) -> TurnCompletionDecision:
    text = request.transcript.strip()
    if not text:
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.9, 18000, "empty transcript")

    if any(phrase in text[-16:] for phrase in THINKING_PHRASES):
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.86, 20000, "thinking phrase")

    if any(text.endswith(ending) for ending in OPEN_ENDINGS):
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.82, 15000, "open-ended phrase")

    if len(text) < 8:
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.68, 4200, "very short answer")

    if len(text) < 16:
        return TurnCompletionDecision(CompletionStatus.UNCERTAIN, 0.52, 3600, "short ambiguous answer")

    if text[-1:] in ".!?;:。！？；" and len(text) >= 20:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.82, 0, "sentence-ending punctuation")

    if len(text) >= 80 and request.pause_ms >= 1100:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.78, 0, "long answer with pause")

    if len(text) >= 28 and request.pause_ms >= 950:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.76, 0, "answer-length pause")

    return TurnCompletionDecision(CompletionStatus.UNCERTAIN, 0.5, 3600, "ambiguous pause")
