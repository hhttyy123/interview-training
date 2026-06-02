import pytest

from app.session.turn_completion import (
    CompletionStatus,
    TurnCompletionDecision,
    TurnCompletionJudge,
    TurnCompletionRequest,
)
from app.session.turn_controller import TurnAction, TurnController


class CompleteJudge(TurnCompletionJudge):
    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.9, 0, "complete enough")


class IncompleteJudge(TurnCompletionJudge):
    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        return TurnCompletionDecision(CompletionStatus.INCOMPLETE, 0.9, 18000, "thinking")


class AmbiguousJudge(TurnCompletionJudge):
    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        return TurnCompletionDecision(CompletionStatus.UNCERTAIN, 0.5, 5500, "ambiguous pause")


class StaleCompleteJudge(TurnCompletionJudge):
    def __init__(self, controller: TurnController) -> None:
        self.controller = controller

    async def judge(self, request: TurnCompletionRequest) -> TurnCompletionDecision:
        self.controller.observe_audio(has_voice=True, now=3.0)
        return TurnCompletionDecision(CompletionStatus.COMPLETE, 0.95, 0, "stale complete")


@pytest.mark.anyio
async def test_turn_controller_ends_when_judge_is_confident_complete() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript("I led the project and shipped the result.", now=1.1)
    controller.observe_audio(has_voice=False, now=2.1)

    action = await controller.next_action(
        judge=CompleteJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )

    assert action.action is TurnAction.END
    assert action.reason == "complete enough"


@pytest.mark.anyio
async def test_turn_controller_waits_when_judge_thinks_user_is_not_done() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript("I am thinking about the metric", now=1.1)
    controller.observe_audio(has_voice=False, now=2.1)

    action = await controller.next_action(
        judge=IncompleteJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )

    assert action.action is TurnAction.WAITING
    assert action.wait_ms == 18000
    assert action.hint_after_ms == 13000
    assert action.trace is not None
    assert action.trace.judge_status == "incomplete"
    assert action.trace.wait_ms == 18000


@pytest.mark.anyio
async def test_turn_controller_emits_hint_and_end_after_wait_window() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript("I am thinking about the metric", now=1.1)
    controller.observe_audio(has_voice=False, now=2.1)

    waiting = await controller.next_action(
        judge=IncompleteJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )
    assert waiting.action is TurnAction.WAITING

    hint = await controller.next_action(
        judge=IncompleteJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=15.8,
    )
    assert hint.action is TurnAction.HINT

    ended = await controller.next_action(
        judge=IncompleteJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=21.0,
    )
    assert ended.action is TurnAction.END


@pytest.mark.anyio
async def test_turn_controller_ignores_stale_judge_result_after_user_speaks() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript("I handled the launch by", now=1.1)
    controller.observe_audio(has_voice=False, now=2.1)

    action = await controller.next_action(
        judge=StaleCompleteJudge(controller),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )

    assert action.action is TurnAction.NONE


@pytest.mark.anyio
async def test_turn_controller_uses_shorter_dynamic_wait_for_ambiguous_long_answer() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript(
        "I owned the rollout, aligned engineering and operations, and tracked conversion after launch",
        now=1.1,
    )
    controller.observe_audio(has_voice=False, now=2.1)

    action = await controller.next_action(
        judge=AmbiguousJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )

    assert action.action is TurnAction.WAITING
    assert action.wait_ms == 2800
    assert action.trace is not None
    assert action.trace.reason == "ambiguous pause"


@pytest.mark.anyio
async def test_turn_controller_can_end_soft_wait_before_full_window() -> None:
    controller = TurnController()
    controller.observe_audio(has_voice=True, now=1.0)
    controller.observe_transcript("I led the rollout with operations and improved conversion", now=1.1)
    controller.observe_audio(has_voice=False, now=2.1)

    waiting = await controller.next_action(
        judge=AmbiguousJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=2.6,
    )
    assert waiting.action is TurnAction.WAITING

    ended = await controller.next_action(
        judge=AmbiguousJudge(),
        messages=[],
        mode_id="standard",
        competency_id="requirement_analysis",
        now=5.3,
    )
    assert ended.action is TurnAction.END
    assert ended.reason == "soft wait resolved"
