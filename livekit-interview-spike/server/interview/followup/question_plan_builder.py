from __future__ import annotations

from interview.followup.models import (
    CareerProfile,
    EvidenceSlot,
    InterviewStage,
    InterviewStyleId,
    QuestionAnchor,
    QuestionConstraints,
    QuestionPlan,
    StrategySelectionResult,
)


def build_question_plan(
    *,
    turn_index: int,
    stage: InterviewStage,
    competency_id: str,
    competency_name: str,
    interview_style_id: InterviewStyleId,
    career_profile: CareerProfile,
    evidence_slots: list[EvidenceSlot],
    selection: StrategySelectionResult,
    last_answer: str = "",
) -> QuestionPlan:
    strategy = selection.selected
    missing = tuple(slot for slot in evidence_slots if slot.status in ("missing", "mentioned", "partial"))
    covered = tuple(slot for slot in evidence_slots if slot.status in ("supported", "strong"))
    target_slots = tuple(slot for slot in missing if slot.category in strategy.applicable_evidence_categories)
    anchor = _build_anchor(last_answer=last_answer, career_profile=career_profile, turn_index=turn_index)
    question_shape = strategy.question_shapes[0] if strategy.question_shapes else "clarify_reference"
    ask_intent = _build_ask_intent(strategy_id=strategy.id, target_slots=target_slots, competency_name=competency_name)

    return QuestionPlan(
        question_id=f"q_{turn_index:03d}",
        turn_index=turn_index,
        stage=stage,
        competency_id=competency_id,
        competency_name=competency_name,
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        methodology_ids=strategy.methodology_ids,
        interview_style_id=interview_style_id,
        question_style_id=strategy.question_style_id,
        pressure_level=strategy.pressure_level,
        anchor=anchor,
        expected_evidence=strategy.expected_evidence,
        missing_evidence_before_question=missing,
        covered_evidence_before_question=covered,
        ask_intent=ask_intent,
        question_shape=question_shape,
        constraints=QuestionConstraints(),
        prompt_hints=strategy.prompt_hints,
        disallowed_moves=strategy.disallowed_moves,
    )


def _build_anchor(*, last_answer: str, career_profile: CareerProfile, turn_index: int) -> QuestionAnchor:
    stripped = last_answer.strip()
    if stripped:
        return QuestionAnchor(
            source="last_answer",
            summary=stripped[:80],
            quote=stripped[:80],
            turn_index=max(0, turn_index - 1),
            confidence="high",
        )
    if career_profile.role_title:
        return QuestionAnchor(
            source="job_model",
            summary=f"target role: {career_profile.role_title}",
            confidence="medium",
        )
    return QuestionAnchor(source="interview_stage", summary="current interview stage", confidence="low")


def _build_ask_intent(*, strategy_id: str, target_slots: tuple[EvidenceSlot, ...], competency_name: str) -> str:
    if target_slots:
        labels = ", ".join(slot.label for slot in target_slots[:3])
        return f"Use {strategy_id} to collect stronger evidence for {competency_name}: {labels}."
    return f"Use {strategy_id} to deepen evidence for {competency_name}."
