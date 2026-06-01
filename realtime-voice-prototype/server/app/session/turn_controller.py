import time
from dataclasses import dataclass
from enum import Enum

from app.session.state import ConversationMessage
from app.session.turn_completion import (
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
    hint_after_ms: int = 0
    hint_text: str = ""
    reason: str = ""


class TurnController:
    no_voice_before_judge_ms = 900
    transcript_stable_ms = 500
    hint_window_ms = 5000
    default_uncertain_wait_ms = 12000
    default_incomplete_wait_ms = 18000

    def __init__(self) -> None:
        self.active = False
        self.revision = 0
        self.started_at = 0.0
        self.last_voice_at = 0.0
        self.last_transcript_at = 0.0
        self.transcript = ""
        self.wait_until = 0.0
        self.hint_at = 0.0
        self.hint_sent = False
        self.pending_judge = False

    def observe_audio(self, *, has_voice: bool, now: float | None = None) -> None:
        now = now or time.monotonic()
        if has_voice:
            self.revision += 1
            if not self.active:
                self.started_at = now
            self.active = True
            self.last_voice_at = now
            self.wait_until = 0.0
            self.hint_at = 0.0
            self.hint_sent = False

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
        self.hint_at = 0.0
        self.hint_sent = False
        self.pending_judge = False

    async def next_action(
        self,
        *,
        judge: TurnCompletionJudge,
        messages: list[ConversationMessage],
        mode_id: str,
        competency_id: str,
        now: float | None = None,
    ) -> TurnControllerAction:
        now = now or time.monotonic()
        if not self.active:
            return TurnControllerAction(TurnAction.NONE)

        if self.wait_until:
            if now >= self.wait_until:
                return TurnControllerAction(TurnAction.END, reason="wait expired")
            if self.hint_at and now >= self.hint_at and not self.hint_sent:
                self.hint_sent = True
                return TurnControllerAction(
                    TurnAction.HINT,
                    wait_ms=int((self.wait_until - now) * 1000),
                    hint_text="If there is nothing to add, I will continue to the next question.",
                    reason="last wait window",
                )
            return TurnControllerAction(TurnAction.NONE)

        pause_ms = int((now - self.last_voice_at) * 1000)
        stable_ms = int((now - max(self.last_transcript_at, self.started_at)) * 1000)
        if pause_ms < self.no_voice_before_judge_ms or stable_ms < self.transcript_stable_ms:
            return TurnControllerAction(TurnAction.NONE)

        if self.pending_judge:
            return TurnControllerAction(TurnAction.NONE)

        self.pending_judge = True
        request_revision = self.revision
        request = TurnCompletionRequest(
            transcript=self.transcript,
            pause_ms=pause_ms,
            utterance_duration_ms=int((now - self.started_at) * 1000),
            messages=messages,
            mode_id=mode_id,
            competency_id=competency_id,
        )
        try:
            decision = await judge.judge(request)
        except Exception:
            decision = TurnCompletionDecision(
                CompletionStatus.UNCERTAIN,
                0.5,
                self.default_uncertain_wait_ms,
                "judge failed",
            )
        finally:
            self.pending_judge = False
        if request_revision != self.revision:
            return TurnControllerAction(TurnAction.NONE)
        return self._action_from_decision(decision, now=now)

    def _action_from_decision(
        self,
        decision: TurnCompletionDecision,
        *,
        now: float | None = None,
    ) -> TurnControllerAction:
        if decision.completion is CompletionStatus.COMPLETE and decision.confidence >= 0.75:
            return TurnControllerAction(TurnAction.END, reason=decision.reason)

        wait_ms = decision.suggested_wait_ms
        if decision.completion is CompletionStatus.COMPLETE:
            wait_ms = wait_ms or 2500
        elif decision.completion is CompletionStatus.INCOMPLETE:
            wait_ms = wait_ms or self.default_incomplete_wait_ms
        else:
            wait_ms = wait_ms or self.default_uncertain_wait_ms

        wait_ms = max(2000, min(wait_ms, 20000))
        now = now or time.monotonic()
        self.wait_until = now + (wait_ms / 1000)
        self.hint_at = self.wait_until - (self.hint_window_ms / 1000)
        self.hint_sent = False
        return TurnControllerAction(
            TurnAction.WAITING,
            wait_ms=wait_ms,
            hint_after_ms=max(0, wait_ms - self.hint_window_ms),
            hint_text="If there is nothing to add, I will continue to the next question.",
            reason=decision.reason,
        )
