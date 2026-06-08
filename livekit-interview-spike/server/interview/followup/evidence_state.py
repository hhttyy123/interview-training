from __future__ import annotations

from interview.followup.models import EvidenceRef, EvidenceSlot, EvidenceUpdate


EMPTY_SIGNAL_WORDS = ("不错", "还可以", "很多", "比较好", "挺好", "有效果")
METRIC_SIGNAL_WORDS = ("%", "数据", "指标", "提升", "降低", "增长", "转化", "留存", "时长")
ACTION_SIGNAL_WORDS = ("我负责", "我做", "我推动", "我设计", "我分析", "我协调", "我优化")
REFLECTION_SIGNAL_WORDS = ("复盘", "反思", "如果重做", "下次", "改进", "不足")


def build_initial_evidence_state(competency_id: str, signals: tuple[str, ...]) -> list[EvidenceSlot]:
    slots: list[EvidenceSlot] = []
    for index, signal in enumerate(signals):
        slots.append(
            EvidenceSlot(
                id=f"{competency_id}_slot_{index}",
                competency_id=competency_id,
                label=signal,
                category=_guess_category(signal),
                required=True,
                priority=max(20, 80 - index * 5),
            )
        )
    return slots


def update_evidence_state_with_answer(
    slots: list[EvidenceSlot],
    *,
    answer: str,
    turn_index: int,
) -> tuple[list[EvidenceSlot], list[EvidenceUpdate]]:
    """Lightweight evidence updater until the LLM evidence judge is added.

    This intentionally treats rules as weak signals. Later phases should replace
    the status decision with an LLM evidence judge and keep these rules as hints.
    """
    updates: list[EvidenceUpdate] = []
    stripped = answer.strip()
    if not stripped:
        return slots, updates

    for slot in slots:
        confidence = _heuristic_confidence(slot, stripped)
        if confidence <= slot.confidence:
            continue
        status = _status_from_confidence(confidence)
        slot.status = status
        slot.confidence = confidence
        slot.refs.append(
            EvidenceRef(
                turn_index=turn_index,
                source="answer",
                excerpt=_excerpt(stripped),
                interpreted_as=slot.label,
                confidence=confidence,
            )
        )
        updates.append(
            EvidenceUpdate(
                slot_id=slot.id,
                status=status,
                confidence=confidence,
                excerpt=_excerpt(stripped),
                rationale="Weak rule signal; replace with LLM evidence judge in the next phase.",
            )
        )
    return slots, updates


def _guess_category(signal: str):
    if any(word in signal for word in ("指标", "数据", "结果", "影响", "转化")):
        return "metric"
    if any(word in signal for word in ("动作", "负责", "推进", "执行", "设计")):
        return "action"
    if any(word in signal for word in ("取舍", "决策", "优先级", "判断")):
        return "decision"
    if any(word in signal for word in ("复盘", "反思", "改进")):
        return "learning"
    if any(word in signal for word in ("协作", "沟通", "跨团队")):
        return "collaboration"
    return "context"


def _heuristic_confidence(slot: EvidenceSlot, answer: str) -> float:
    confidence = 0.0
    if slot.label and slot.label[:4] in answer:
        confidence += 0.35
    if slot.category == "metric" and (any(word in answer for word in METRIC_SIGNAL_WORDS) or any(ch.isdigit() for ch in answer)):
        confidence += 0.35
    if slot.category == "action" and any(word in answer for word in ACTION_SIGNAL_WORDS):
        confidence += 0.35
    if slot.category == "learning" and any(word in answer for word in REFLECTION_SIGNAL_WORDS):
        confidence += 0.35
    if any(word in answer for word in EMPTY_SIGNAL_WORDS):
        confidence -= 0.1
    return max(0.0, min(0.75, confidence))


def _status_from_confidence(confidence: float):
    if confidence >= 0.65:
        return "supported"
    if confidence >= 0.35:
        return "partial"
    if confidence > 0:
        return "mentioned"
    return "missing"


def _excerpt(answer: str) -> str:
    return answer[:120]
