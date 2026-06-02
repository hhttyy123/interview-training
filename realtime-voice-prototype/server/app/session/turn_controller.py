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
class TurnDecisionTrace:
    active: bool
    action: str
    pause_ms: int = 0
    stable_ms: int = 0
    transcript_length: int = 0
    judge_status: str = ""
    judge_confidence: float = 0.0
    judge_latency_ms: int = 0
    wait_ms: int = 0
    reason: str = ""


@dataclass(frozen=True)
class TurnControllerAction:
    action: TurnAction
    wait_ms: int = 0
    hint_after_ms: int = 0
    hint_text: str = ""
    reason: str = ""
    trace: TurnDecisionTrace | None = None


class TurnController:
    no_voice_before_judge_ms = 900
    transcript_stable_ms = 500
    hint_window_ms = 5000
    default_uncertain_wait_ms = 12000
    default_incomplete_wait_ms = 18000
    soft_wait_min_ms = 2600

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
        if has_voice:
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
        mode_id: str,
        competency_id: str,
        now: float | None = None,
    ) -> TurnControllerAction:
        now = now or time.monotonic()
        if not self.active:
            return TurnControllerAction(TurnAction.NONE, trace=TurnDecisionTrace(False, "none", reason="inactive"))

        if self.wait_until:
            pause_ms = int((now - self.last_voice_at) * 1000)
            wait_elapsed_ms = int((now - self.wait_started_at) * 1000)
            if self.wait_can_auto_end and wait_elapsed_ms >= self.soft_wait_min_ms and self._transcript_can_soft_end():
                return TurnControllerAction(
                    TurnAction.END,
                    reason="soft wait resolved",
                    trace=TurnDecisionTrace(
                        True,
                        "end",
                        pause_ms=pause_ms,
                        wait_ms=0,
                        transcript_length=len(self.transcript),
                        reason="soft wait resolved",
                    ),
                )
            if now >= self.wait_until:
                return TurnControllerAction(
                    TurnAction.END,
                    reason="wait expired",
                    trace=TurnDecisionTrace(
                        True,
                        "end",
                        wait_ms=0,
                        transcript_length=len(self.transcript),
                        reason="wait expired",
                    ),
                )
            if self.hint_at and now >= self.hint_at and not self.hint_sent:
                self.hint_sent = True
                wait_ms = int((self.wait_until - now) * 1000)
                return TurnControllerAction(
                    TurnAction.HINT,
                    wait_ms=wait_ms,
                    hint_text="\u5982\u679c\u4f60\u6ca1\u6709\u66f4\u591a\u8981\u8865\u5145\u7684\uff0c\u6211\u5c06\u7ee7\u7eed\u4e0b\u4e00\u9898\u3002",
                    reason="last wait window",
                    trace=TurnDecisionTrace(
                        True,
                        "hint",
                        wait_ms=wait_ms,
                        transcript_length=len(self.transcript),
                        reason="last wait window",
                    ),
                )
            return TurnControllerAction(
                TurnAction.NONE,
                trace=TurnDecisionTrace(
                    True,
                    "none",
                    wait_ms=int((self.wait_until - now) * 1000),
                    transcript_length=len(self.transcript),
                    reason="waiting window active",
                ),
            )

        pause_ms = int((now - self.last_voice_at) * 1000)
        stable_ms = int((now - max(self.last_transcript_at, self.started_at)) * 1000)
        if pause_ms < self.no_voice_before_judge_ms or stable_ms < self.transcript_stable_ms:
            return TurnControllerAction(
                TurnAction.NONE,
                trace=TurnDecisionTrace(
                    True,
                    "none",
                    pause_ms=pause_ms,
                    stable_ms=stable_ms,
                    transcript_length=len(self.transcript),
                    reason="pause or transcript not stable",
                ),
            )

        if self.pending_judge:
            return TurnControllerAction(
                TurnAction.NONE,
                trace=TurnDecisionTrace(
                    True,
                    "none",
                    pause_ms=pause_ms,
                    stable_ms=stable_ms,
                    transcript_length=len(self.transcript),
                    reason="judge already pending",
                ),
            )

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
        judge_started_at = time.monotonic()
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
        judge_latency_ms = int((time.monotonic() - judge_started_at) * 1000)
        if request_revision != self.revision:
            return TurnControllerAction(
                TurnAction.NONE,
                trace=TurnDecisionTrace(
                    True,
                    "none",
                    pause_ms=pause_ms,
                    stable_ms=stable_ms,
                    transcript_length=len(self.transcript),
                    judge_status=decision.completion.value,
                    judge_confidence=decision.confidence,
                    judge_latency_ms=judge_latency_ms,
                    reason="stale judge result",
                ),
            )
        return self._action_from_decision(
            decision,
            now=now,
            pause_ms=pause_ms,
            stable_ms=stable_ms,
            judge_latency_ms=judge_latency_ms,
        )

    def _action_from_decision(
        self,
        decision: TurnCompletionDecision,
        *,
        now: float | None = None,
        pause_ms: int = 0,
        stable_ms: int = 0,
        judge_latency_ms: int = 0,
    ) -> TurnControllerAction:
        if decision.completion is CompletionStatus.COMPLETE and decision.confidence >= 0.75:
            return TurnControllerAction(
                TurnAction.END,
                reason=decision.reason,
                trace=self._trace_from_decision(
                    "end",
                    decision,
                    pause_ms=pause_ms,
                    stable_ms=stable_ms,
                    judge_latency_ms=judge_latency_ms,
                    reason=decision.reason,
                ),
            )

        wait_ms = self._wait_ms_for_decision(decision)
        wait_ms = max(2000, min(wait_ms, 20000))
        now = now or time.monotonic()
        self.wait_until = now + (wait_ms / 1000)
        self.wait_started_at = now
        self.hint_at = self.wait_until - (self.hint_window_ms / 1000) if wait_ms > self.hint_window_ms else 0.0
        self.hint_sent = False
        self.wait_can_auto_end = self._can_auto_end_wait(decision)
        return TurnControllerAction(
            TurnAction.WAITING,
            wait_ms=wait_ms,
            hint_after_ms=max(0, wait_ms - self.hint_window_ms),
            hint_text="\u5982\u679c\u4f60\u6ca1\u6709\u66f4\u591a\u8981\u8865\u5145\u7684\uff0c\u6211\u5c06\u7ee7\u7eed\u4e0b\u4e00\u9898\u3002",
            reason=decision.reason,
            trace=self._trace_from_decision(
                "waiting",
                decision,
                pause_ms=pause_ms,
                stable_ms=stable_ms,
                judge_latency_ms=judge_latency_ms,
                wait_ms=wait_ms,
                reason=decision.reason,
            ),
        )

    def _wait_ms_for_decision(self, decision: TurnCompletionDecision) -> int:
        text = self.transcript.strip()
        suggested_wait_ms = decision.suggested_wait_ms

        if decision.completion is CompletionStatus.COMPLETE:
            return suggested_wait_ms or (900 if decision.confidence >= 0.68 else 1800)

        if decision.completion is CompletionStatus.INCOMPLETE:
            if "thinking" in decision.reason or "open-ended" in decision.reason:
                return suggested_wait_ms or self.default_incomplete_wait_ms
            if len(text) < 12:
                return min(suggested_wait_ms or 4500, 4500)
            return min(suggested_wait_ms or 7000, 7000)

        if len(text) >= 60 and decision.confidence >= 0.45:
            return min(suggested_wait_ms or 2800, 2800)
        if len(text) >= 24:
            return min(suggested_wait_ms or 3800, 3800)
        return min(suggested_wait_ms or 5500, 5500)

    def _can_auto_end_wait(self, decision: TurnCompletionDecision) -> bool:
        if decision.completion is CompletionStatus.COMPLETE:
            return True
        if decision.completion is CompletionStatus.UNCERTAIN:
            return True
        return "short answer" in decision.reason

    def _transcript_can_soft_end(self) -> bool:
        text = self.transcript.strip()
        if not text:
            return False
        protected_endings = ("\u7136\u540e", "\u56e0\u4e3a", "\u6bd4\u5982", "\u6211\u89c9\u5f97", "\u8fd9\u4e2a", "\u4e3b\u8981\u662f", "\u6240\u4ee5", "\u800c\u4e14")
        protected_phrases = ("\u6211\u60f3\u4e00\u4e0b", "\u6211\u60f3\u60f3", "\u7b49\u4e00\u4e0b", "\u7a0d\u7b49")
        if any(phrase in text[-12:] for phrase in protected_phrases):
            return False
        return not any(text.endswith(ending) for ending in protected_endings)

    def _trace_from_decision(
        self,
        action: str,
        decision: TurnCompletionDecision,
        *,
        pause_ms: int,
        stable_ms: int,
        judge_latency_ms: int,
        wait_ms: int = 0,
        reason: str,
    ) -> TurnDecisionTrace:
        return TurnDecisionTrace(
            True,
            action,
            pause_ms=pause_ms,
            stable_ms=stable_ms,
            transcript_length=len(self.transcript),
            judge_status=decision.completion.value,
            judge_confidence=decision.confidence,
            judge_latency_ms=judge_latency_ms,
            wait_ms=wait_ms,
            reason=reason,
        )
