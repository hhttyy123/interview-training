import time
from dataclasses import dataclass
from enum import Enum

from local_providers import ConversationMessage
from turn_completion import (
    CompletionStatus,
    TurnCompletionDecision,
    TurnCompletionJudge,
    TurnCompletionRequest,
)


class TurnAction(str, Enum):
    NONE = "none"
    END = "end"
    WAITING = "waiting"
    HINT = "hint"


@dataclass(frozen=True)
class TurnControllerAction:
    action: TurnAction
    wait_ms: int = 0
    hint_text: str = ""
    reason: str = ""


class TurnController:
    no_voice_before_judge_ms = 650
    transcript_stable_ms = 350
    hint_window_ms = 5000
    soft_wait_min_ms = 1500

    def __init__(self) -> None:
        self.active = False
        self.revision = 0
        self.started_at = 0.0
        self.last_voice_at = 0.0
        self.last_transcript_at = 0.0
        self.transcript = ""
        self.wait_until = 0.0
        self.wait_started_at = 0.0
        self.hint_at = 0.0
        self.hint_sent = False
        self.wait_can_auto_end = False
        self.pending_judge = False

    def observe_audio(self, *, has_voice: bool, now: float | None = None) -> None:
        now = now or time.monotonic()
        if not has_voice:
            return

        self.revision += 1
        if not self.active:
            self.started_at = now
        self.active = True
        self.last_voice_at = now
        self.wait_until = 0.0
        self.wait_started_at = 0.0
        self.hint_at = 0.0
        self.hint_sent = False
        self.wait_can_auto_end = False

    def observe_transcript(self, text: str, *, now: float | None = None) -> None:
        now = now or time.monotonic()
        if text != self.transcript:
            self.revision += 1
            self.transcript = text
            self.last_transcript_at = now

    def reset_turn(self) -> None:
        self.active = False
        self.revision += 1
        self.started_at = 0.0
        self.last_voice_at = 0.0
        self.last_transcript_at = 0.0
        self.transcript = ""
        self.wait_until = 0.0
        self.wait_started_at = 0.0
        self.hint_at = 0.0
        self.hint_sent = False
        self.wait_can_auto_end = False
        self.pending_judge = False

    async def next_action(
        self,
        *,
        judge: TurnCompletionJudge,
        messages: list[ConversationMessage],
        now: float | None = None,
    ) -> TurnControllerAction:
        now = now or time.monotonic()
        if not self.active:
            return TurnControllerAction(TurnAction.NONE, reason="inactive")

        if self.wait_until:
            if self.wait_can_auto_end and now - self.wait_started_at >= self.soft_wait_min_ms / 1000:
                if self._transcript_can_soft_end():
                    return TurnControllerAction(TurnAction.END, reason="soft wait resolved")

            if now >= self.wait_until:
                return TurnControllerAction(TurnAction.END, reason="wait expired")

            if self.hint_at and now >= self.hint_at and not self.hint_sent:
                self.hint_sent = True
                return TurnControllerAction(
                    TurnAction.HINT,
                    wait_ms=int((self.wait_until - now) * 1000),
                    hint_text="如果你还在思考，我会再等一下；如果没有更多补充，我将继续追问。",
                    reason="last wait window",
                )

            return TurnControllerAction(
                TurnAction.NONE,
                wait_ms=int((self.wait_until - now) * 1000),
                reason="waiting window active",
            )

        pause_ms = int((now - self.last_voice_at) * 1000)
        stable_ms = int((now - max(self.last_transcript_at, self.started_at)) * 1000)
        if pause_ms < self.no_voice_before_judge_ms or stable_ms < self.transcript_stable_ms:
            return TurnControllerAction(TurnAction.NONE, reason="pause or transcript not stable")

        if self.pending_judge:
            return TurnControllerAction(TurnAction.NONE, reason="judge already pending")

        self.pending_judge = True
        request_revision = self.revision
        request = TurnCompletionRequest(
            transcript=self.transcript,
            pause_ms=pause_ms,
            utterance_duration_ms=int((now - self.started_at) * 1000),
            messages=messages,
        )
        try:
            decision = await judge.judge(request)
        finally:
            self.pending_judge = False

        if request_revision != self.revision:
            return TurnControllerAction(TurnAction.NONE, reason="stale judge result")

        return self._action_from_decision(decision, now=now)

    def _action_from_decision(
        self,
        decision: TurnCompletionDecision,
        *,
        now: float,
    ) -> TurnControllerAction:
        if decision.completion is CompletionStatus.COMPLETE and decision.confidence >= 0.74:
            return TurnControllerAction(TurnAction.END, reason=decision.reason)

        wait_ms = max(2000, min(self._wait_ms_for_decision(decision), 20000))
        self.wait_until = now + wait_ms / 1000
        self.wait_started_at = now
        self.hint_at = self.wait_until - self.hint_window_ms / 1000 if wait_ms > self.hint_window_ms else 0.0
        self.hint_sent = False
        self.wait_can_auto_end = decision.completion is not CompletionStatus.INCOMPLETE
        return TurnControllerAction(
            TurnAction.WAITING,
            wait_ms=wait_ms,
            hint_text="如果你还在思考，我会再等一下；如果没有更多补充，我将继续追问。",
            reason=decision.reason,
        )

    def _wait_ms_for_decision(self, decision: TurnCompletionDecision) -> int:
        text = self.transcript.strip()
        if decision.completion is CompletionStatus.COMPLETE:
            return decision.suggested_wait_ms or 900
        if decision.completion is CompletionStatus.INCOMPLETE:
            if len(text) < 12 and "thinking" not in decision.reason:
                return min(decision.suggested_wait_ms or 4500, 4500)
            return decision.suggested_wait_ms or 16000
        if len(text) >= 60:
            return min(decision.suggested_wait_ms or 1800, 1800)
        if len(text) >= 24:
            return min(decision.suggested_wait_ms or 2600, 2600)
        return min(decision.suggested_wait_ms or 3600, 3600)

    def _transcript_can_soft_end(self) -> bool:
        text = self.transcript.strip()
        if not text:
            return False
        protected_endings = ("然后", "因为", "比如", "我觉得", "这个", "主要是", "所以", "而且", "但是", "另外")
        protected_phrases = ("我想一下", "我想想", "等一下", "稍等", "让我想", "我思考")
        if any(phrase in text[-16:] for phrase in protected_phrases):
            return False
        return not any(text.endswith(ending) for ending in protected_endings)
