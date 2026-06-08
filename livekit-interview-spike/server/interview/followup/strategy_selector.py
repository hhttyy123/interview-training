from __future__ import annotations

from collections import Counter

from interview.followup.models import (
    CareerProfile,
    EvidenceSlot,
    FollowUpStrategy,
    InterviewStage,
    InterviewStyleId,
    StrategySelectionResult,
)
from interview.followup.strategy_library import DEFAULT_FOLLOW_UP_STRATEGIES


def select_followup_strategy(
    *,
    stage: InterviewStage,
    interview_style_id: InterviewStyleId,
    evidence_slots: list[EvidenceSlot],
    career_profile: CareerProfile,
    recent_strategy_ids: tuple[str, ...] = (),
    strategies: tuple[FollowUpStrategy, ...] = DEFAULT_FOLLOW_UP_STRATEGIES,
) -> StrategySelectionResult:
    candidates: list[tuple[FollowUpStrategy, float, dict[str, float]]] = []
    for strategy in strategies:
        score, breakdown = _score_strategy(
            strategy=strategy,
            stage=stage,
            interview_style_id=interview_style_id,
            evidence_slots=evidence_slots,
            career_profile=career_profile,
            recent_strategy_ids=recent_strategy_ids,
        )
        if score > 0:
            candidates.append((strategy, score, breakdown))

    if not candidates:
        fallback = DEFAULT_FOLLOW_UP_STRATEGIES[-1]
        return StrategySelectionResult(
            selected=fallback,
            score=1.0,
            score_breakdown={"fallback": 1.0},
            selected_because="No scored strategy matched; using recovery fallback.",
        )

    candidates.sort(key=lambda item: item[1], reverse=True)
    selected, score, breakdown = candidates[0]
    alternatives = tuple((item[0].id, item[1], _reason_not_selected(item[0], selected)) for item in candidates[1:4])
    return StrategySelectionResult(
        selected=selected,
        score=score,
        score_breakdown=breakdown,
        selected_because=_selected_reason(selected, breakdown),
        alternatives=alternatives,
    )


def _score_strategy(
    *,
    strategy: FollowUpStrategy,
    stage: InterviewStage,
    interview_style_id: InterviewStyleId,
    evidence_slots: list[EvidenceSlot],
    career_profile: CareerProfile,
    recent_strategy_ids: tuple[str, ...],
) -> tuple[float, dict[str, float]]:
    breakdown: dict[str, float] = {}

    if stage in strategy.applicable_stages:
        breakdown["stage"] = 20.0
    elif "middle" in strategy.applicable_stages:
        breakdown["stage"] = 8.0
    else:
        return 0.0, {}

    if interview_style_id in strategy.preferred_styles:
        breakdown["style"] = 18.0
    elif interview_style_id == "pressure" and strategy.pressure_level > 0:
        breakdown["style"] = 12.0
    else:
        breakdown["style"] = 4.0

    gap_score = 0.0
    for slot in evidence_slots:
        if slot.category not in strategy.applicable_evidence_categories:
            continue
        if slot.status == "missing":
            gap_score += 16 + slot.priority / 10
        elif slot.status in ("mentioned", "partial"):
            gap_score += 10 + slot.priority / 20
        elif slot.status == "contradictory":
            gap_score += 18
    breakdown["evidence_gap"] = min(35.0, gap_score)

    if career_profile.role_family in strategy.applicable_role_families or "general" in strategy.applicable_role_families:
        breakdown["career_fit"] = 10.0
    else:
        breakdown["career_fit"] = 3.0

    recent_counts = Counter(recent_strategy_ids)
    repetition_penalty = recent_counts[strategy.id] * 12.0
    if recent_strategy_ids[-1:] == (strategy.id,):
        repetition_penalty += 10.0
    breakdown["repetition_penalty"] = -repetition_penalty

    if strategy.category == "pressure" and interview_style_id == "supportive":
        breakdown["risk_penalty"] = -15.0

    return sum(breakdown.values()), breakdown


def _selected_reason(strategy: FollowUpStrategy, breakdown: dict[str, float]) -> str:
    top = sorted(((key, value) for key, value in breakdown.items() if value > 0), key=lambda item: item[1], reverse=True)
    reasons = ", ".join(key for key, _ in top[:3])
    return f"Selected {strategy.id} based on {reasons or 'fallback scoring'}."


def _reason_not_selected(strategy: FollowUpStrategy, selected: FollowUpStrategy) -> str:
    if strategy.category == selected.category:
        return "Lower score within the same strategy category."
    return f"Lower score than selected strategy {selected.id}."
