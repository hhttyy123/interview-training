from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from interview.followup.models import EvidenceSlot, QuestionPlan, QuestionTraceDecision


@dataclass(frozen=True)
class EvaluationTurn:
    turn_index: int
    question: str
    answer: str
    capability_id: str
    question_style_id: str


@dataclass(frozen=True)
class EvaluationQuestionTraceItem:
    question_id: str
    turn_index: int
    question: str
    stage: str
    competency_id: str
    competency_name: str
    strategy_id: str
    strategy_name: str
    methodology_ids: tuple[str, ...]
    methodology_notes: tuple[str, ...]
    question_style_id: str
    interview_style_id: str
    pressure_level: int
    anchor: dict[str, Any]
    evidence_target_ids: tuple[str, ...]
    missing_evidence_before_question: tuple[dict[str, Any], ...]
    covered_evidence_before_question: tuple[dict[str, Any], ...]
    selected_because: str = ""
    alternatives_considered: tuple[tuple[str, float, str], ...] = ()


@dataclass(frozen=True)
class EvaluationEvidenceSnapshot:
    slots: tuple[dict[str, Any], ...]
    coverage_ratio: float = 0.0
    source: str = "followup_strategy_library"


@dataclass(frozen=True)
class EvaluationRequest:
    session_id: str
    target_role: str
    turns: tuple[EvaluationTurn, ...]
    question_trace: tuple[EvaluationQuestionTraceItem, ...]
    evidence_snapshot: EvaluationEvidenceSnapshot
    company_card: dict[str, Any] | None = None
    career_profile: dict[str, Any] | None = None
    job_model: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationDimensionResult:
    id: str
    name: str
    score: int | None
    level: str
    reason: str
    evidence: str
    risk: str = ""
    improvement: str = ""


@dataclass(frozen=True)
class EvaluationResponse:
    report_quality: str
    summary: str
    dimensions: tuple[EvaluationDimensionResult, ...]
    evidence_gaps: tuple[str, ...]
    ability_model: dict[str, int]
    company_fit_bonus: dict[str, Any] | None = None
    role_fit: dict[str, Any] | None = None
    main_weakness: str = ""
    training_plan: dict[str, Any] | None = None


def question_trace_item_from_plan(
    *,
    plan: QuestionPlan,
    question: str,
    decision: QuestionTraceDecision | None = None,
) -> EvaluationQuestionTraceItem:
    return EvaluationQuestionTraceItem(
        question_id=plan.question_id,
        turn_index=plan.turn_index,
        question=question,
        stage=plan.stage,
        competency_id=plan.competency_id,
        competency_name=plan.competency_name,
        strategy_id=plan.strategy_id,
        strategy_name=plan.strategy_name,
        methodology_ids=plan.methodology_ids,
        methodology_notes=plan.methodology_notes,
        question_style_id=plan.question_style_id,
        interview_style_id=plan.interview_style_id,
        pressure_level=plan.pressure_level,
        anchor=asdict(plan.anchor),
        evidence_target_ids=tuple(slot.id for slot in plan.missing_evidence_before_question[:5]),
        missing_evidence_before_question=tuple(_slot_snapshot(slot) for slot in plan.missing_evidence_before_question),
        covered_evidence_before_question=tuple(_slot_snapshot(slot) for slot in plan.covered_evidence_before_question),
        selected_because=decision.selected_because if decision else "",
        alternatives_considered=decision.alternatives if decision else (),
    )


def evidence_snapshot_from_slots(
    *,
    slots: list[EvidenceSlot],
) -> EvaluationEvidenceSnapshot:
    if not slots:
        return EvaluationEvidenceSnapshot(slots=(), coverage_ratio=0.0)
    covered = sum(1 for slot in slots if slot.status in ("supported", "strong"))
    return EvaluationEvidenceSnapshot(
        slots=tuple(_slot_snapshot(slot) for slot in slots),
        coverage_ratio=round(covered / len(slots), 3),
    )


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value


def _slot_snapshot(slot: EvidenceSlot) -> dict[str, Any]:
    return {
        "id": slot.id,
        "competency_id": slot.competency_id,
        "label": slot.label,
        "category": slot.category,
        "required": slot.required,
        "priority": slot.priority,
        "status": slot.status,
        "confidence": slot.confidence,
        "refs": [asdict(ref) for ref in slot.refs],
        "last_asked_turn": slot.last_asked_turn,
        "ask_count": slot.ask_count,
    }
