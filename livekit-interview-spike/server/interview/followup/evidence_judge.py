from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from interview.followup.models import EvidenceSlot, EvidenceUpdate
from local_providers import ConversationMessage


class CompletionProvider(Protocol):
    async def complete_reply(
        self,
        messages: list[ConversationMessage],
        *,
        system_prompt: str,
        temperature: float = 0.0,
    ) -> str:
        ...


@dataclass(frozen=True)
class RuleEvidenceSignals:
    has_number: bool = False
    has_time: bool = False
    has_role_marker: bool = False
    has_action_marker: bool = False
    has_result_marker: bool = False
    has_comparison_marker: bool = False
    has_reflection_marker: bool = False
    vague_marker_count: int = 0
    answer_length: int = 0


@dataclass(frozen=True)
class EvidenceJudgeResult:
    updates: tuple[EvidenceUpdate, ...]
    rule_signals: RuleEvidenceSignals
    model_rationale: str = ""
    fallback_used: bool = False
    raw_response: str = ""


async def judge_evidence_with_llm(
    *,
    answer: str,
    candidate_slots: list[EvidenceSlot],
    provider: CompletionProvider,
    context_summary: str = "",
) -> EvidenceJudgeResult:
    signals = inspect_rule_evidence_signals(answer)
    prompt = build_evidence_judge_prompt(
        answer=answer,
        candidate_slots=candidate_slots,
        rule_signals=signals,
        context_summary=context_summary,
    )
    raw = await provider.complete_reply(
        [ConversationMessage("user", prompt)],
        system_prompt="你是面试证据质量判断器，只输出合法 JSON，不输出解释。",
        temperature=0.0,
    )
    parsed = _parse_json(raw)
    updates = tuple(_parse_updates(parsed, candidate_slots))
    if not updates:
        return EvidenceJudgeResult(
            updates=tuple(_fallback_updates(answer, candidate_slots, signals)),
            rule_signals=signals,
            model_rationale="LLM 返回可解析 JSON，但没有有效 evidence_updates，已使用规则兜底。",
            fallback_used=True,
            raw_response=raw,
        )
    return EvidenceJudgeResult(
        updates=updates,
        rule_signals=signals,
        model_rationale=str(parsed.get("overall_rationale", "")),
        raw_response=raw,
    )


def judge_evidence_with_rules(
    *,
    answer: str,
    candidate_slots: list[EvidenceSlot],
) -> EvidenceJudgeResult:
    signals = inspect_rule_evidence_signals(answer)
    return EvidenceJudgeResult(
        updates=tuple(_fallback_updates(answer, candidate_slots, signals)),
        rule_signals=signals,
        model_rationale="LLM 不可用，使用规则兜底；该结果只能作为弱信号。",
        fallback_used=True,
    )


def apply_evidence_updates(
    *,
    slots: list[EvidenceSlot],
    updates: tuple[EvidenceUpdate, ...],
) -> list[EvidenceSlot]:
    update_by_id = {update.slot_id: update for update in updates}
    next_slots: list[EvidenceSlot] = []
    for slot in slots:
        update = update_by_id.get(slot.id)
        if update is None:
            next_slots.append(slot)
            continue
        slot.status = update.status
        slot.confidence = update.confidence
        if update.excerpt:
            from interview.followup.models import EvidenceRef

            slot.refs.append(
                EvidenceRef(
                    turn_index=-1,
                    source="answer",
                    excerpt=update.excerpt[:180],
                    interpreted_as=update.rationale,
                    confidence=update.confidence,
                )
            )
        next_slots.append(slot)
    return next_slots


def inspect_rule_evidence_signals(answer: str) -> RuleEvidenceSignals:
    text = answer.strip()
    return RuleEvidenceSignals(
        has_number=bool(re.search(r"\d+|一|二|三|四|五|六|七|八|九|十|百|千|万|%|％", text)),
        has_time=bool(re.search(r"\d+\s*(天|周|月|年|小时|分钟)|当时|后来|上线后|迭代后", text)),
        has_role_marker=bool(re.search(r"我负责|我主导|我参与|我推动|我的角色|由我", text)),
        has_action_marker=bool(re.search(r"做了|推进|设计|分析|协调|沟通|落地|优化|验证|排查", text)),
        has_result_marker=bool(re.search(r"结果|提升|降低|增长|减少|完成|上线|通过|转化|留存", text)),
        has_comparison_marker=bool(re.search(r"之前|之后|相比|从.+到|对比|基线", text)),
        has_reflection_marker=bool(re.search(r"复盘|反思|下次|改进|学到|经验", text)),
        vague_marker_count=len(re.findall(r"还可以|不错|很多|比较好|有一些|大概|差不多|感觉", text)),
        answer_length=len(text),
    )


def build_evidence_judge_prompt(
    *,
    answer: str,
    candidate_slots: list[EvidenceSlot],
    rule_signals: RuleEvidenceSignals,
    context_summary: str = "",
) -> str:
    slots_payload = [
        {
            "slot_id": slot.id,
            "competency_id": slot.competency_id,
            "label": slot.label,
            "category": slot.category,
            "current_status": slot.status,
            "quality_bar": {
                "unacceptable": slot.quality_bar.unacceptable,
                "weak": slot.quality_bar.weak,
                "acceptable": slot.quality_bar.acceptable,
                "strong": slot.quality_bar.strong,
            }
            if slot.quality_bar
            else None,
        }
        for slot in candidate_slots
    ]
    return json.dumps(
        {
            "task": "判断候选人回答是否为每个 evidence slot 提供了有效证据。LLM 是主判断，规则信号只作辅助，不要机械套规则。",
            "context_summary": context_summary,
            "candidate_answer": answer,
            "rule_signals": rule_signals.__dict__,
            "candidate_slots": slots_payload,
            "output_schema": {
                "overall_rationale": "简短说明整体证据质量",
                "evidence_updates": [
                    {
                        "slot_id": "必须来自 candidate_slots",
                        "status": "missing | mentioned | partial | supported | strong | contradictory",
                        "confidence": "0.0 到 1.0",
                        "excerpt": "回答中的短证据片段，没有则为空",
                        "rationale": "为什么这样判断",
                        "next_best_probe": "如果证据不足，下一步最好追问什么",
                    }
                ],
            },
            "rules": [
                "不要因为出现数字就自动判 strong，必须判断数字是否和该证据槽有关。",
                "不要因为回答短就自动判 missing，短回答如果具体也可以 supported。",
                "如果只出现空泛评价，通常最多 mentioned 或 partial。",
                "如果回答能说明场景、个人动作、结果、边界或复盘，可提升到 supported/strong。",
                "没有被回答覆盖的 slot 不必全部返回，只返回需要更新或有明显判断价值的 slot。",
            ],
        },
        ensure_ascii=False,
    )


def _parse_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Evidence judge response must be a JSON object")
    return payload


def _parse_updates(payload: dict[str, Any], candidate_slots: list[EvidenceSlot]) -> list[EvidenceUpdate]:
    valid_slot_ids = {slot.id for slot in candidate_slots}
    updates: list[EvidenceUpdate] = []
    raw_updates = payload.get("evidence_updates", [])
    if not isinstance(raw_updates, list):
        return updates
    for item in raw_updates:
        if not isinstance(item, dict):
            continue
        slot_id = str(item.get("slot_id", ""))
        status = str(item.get("status", "missing"))
        if slot_id not in valid_slot_ids or status not in VALID_STATUSES:
            continue
        updates.append(
            EvidenceUpdate(
                slot_id=slot_id,
                status=status,  # type: ignore[arg-type]
                confidence=_clamp_float(item.get("confidence"), 0.0, 1.0),
                excerpt=str(item.get("excerpt", ""))[:180],
                rationale=str(item.get("rationale", "")),
                next_best_probe=str(item.get("next_best_probe", "")),
            )
        )
    return updates


def _fallback_updates(
    answer: str,
    candidate_slots: list[EvidenceSlot],
    signals: RuleEvidenceSignals,
) -> list[EvidenceUpdate]:
    if not answer.strip():
        return []
    status = "mentioned"
    confidence = 0.35
    if signals.has_action_marker and (signals.has_result_marker or signals.has_number):
        status = "partial"
        confidence = 0.5
    if signals.has_role_marker and signals.has_action_marker and signals.has_result_marker and signals.has_number:
        status = "supported"
        confidence = 0.68
    if signals.vague_marker_count >= 2:
        confidence = max(0.2, confidence - 0.15)
    return [
        EvidenceUpdate(
            slot_id=slot.id,
            status=status,  # type: ignore[arg-type]
            confidence=confidence,
            excerpt=answer.strip()[:180],
            rationale="规则兜底：仅根据显性信号生成弱判断，需要 LLM evidence judge 复核。",
            next_best_probe=f"请补充{slot.label}中最具体的一段事实、动作或结果。",
        )
        for slot in candidate_slots[:3]
    ]


def _clamp_float(value: Any, min_value: float, max_value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return min_value
    return max(min_value, min(max_value, number))


VALID_STATUSES = {"missing", "mentioned", "partial", "supported", "strong", "contradictory"}
