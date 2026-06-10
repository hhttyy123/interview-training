from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from local_providers import ConversationMessage


ANSWER_GAP_TYPES = {
    "too_generic",
    "missing_context",
    "missing_task",
    "missing_action",
    "missing_result",
    "missing_metric",
    "missing_reflection",
    "missing_tradeoff",
    "missing_technical_depth",
    "weak_attribution",
    "off_topic",
    "sufficient_for_now",
}


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
class AnswerGapAnalysis:
    gap_types: tuple[str, ...]
    evidence_status: dict[str, str] = field(default_factory=dict)
    specificity_level: str = "unknown"
    answer_quality_summary: str = ""
    best_next_probe_target: str = ""
    risk_flags: tuple[str, ...] = ()
    confidence: float = 0.4
    fallback_used: bool = False
    raw_response: str = ""


async def analyze_answer_gap_with_llm(
    *,
    provider: CompletionProvider,
    role_name: str,
    competency_name: str,
    question_style_id: str,
    previous_question: str,
    answer: str,
    missing_evidence: tuple[str, ...],
    recent_turns: tuple[tuple[str, str], ...] = (),
) -> AnswerGapAnalysis:
    prompt = build_answer_gap_prompt(
        role_name=role_name,
        competency_name=competency_name,
        question_style_id=question_style_id,
        previous_question=previous_question,
        answer=answer,
        missing_evidence=missing_evidence,
        recent_turns=recent_turns,
    )
    raw = await provider.complete_reply(
        [ConversationMessage("user", prompt)],
        system_prompt="You are an interview evidence gap analyzer. Output valid JSON only.",
        temperature=0.0,
    )
    return parse_answer_gap_response(raw)


def build_answer_gap_prompt(
    *,
    role_name: str,
    competency_name: str,
    question_style_id: str,
    previous_question: str,
    answer: str,
    missing_evidence: tuple[str, ...],
    recent_turns: tuple[tuple[str, str], ...] = (),
) -> str:
    recent = [
        {"question": question[-180:], "answer": response[-220:]}
        for question, response in recent_turns[-3:]
    ]
    return json.dumps(
        {
            "task": "Analyze the candidate answer and identify what evidence is still missing for the next follow-up question.",
            "language": "zh-CN",
            "role_name": role_name,
            "competency_name": competency_name,
            "question_style_id": question_style_id,
            "previous_question": previous_question,
            "candidate_answer": answer,
            "current_missing_evidence_from_system": list(missing_evidence),
            "recent_turns": recent,
            "allowed_gap_types": sorted(ANSWER_GAP_TYPES),
            "output_schema": {
                "gap_types": ["one or more allowed_gap_types"],
                "evidence_status": {
                    "context": "missing|mentioned|partial|supported|strong",
                    "task": "missing|mentioned|partial|supported|strong",
                    "action": "missing|mentioned|partial|supported|strong",
                    "result": "missing|mentioned|partial|supported|strong",
                    "metric": "missing|mentioned|partial|supported|strong",
                    "technical_depth": "missing|mentioned|partial|supported|strong",
                    "tradeoff": "missing|mentioned|partial|supported|strong",
                    "reflection": "missing|mentioned|partial|supported|strong",
                },
                "specificity_level": "very_low|low|medium|high",
                "answer_quality_summary": "short Chinese summary",
                "best_next_probe_target": "what the next follow-up should collect",
                "risk_flags": ["possible issues such as overclaim, off_topic, too_short"],
                "confidence": "0.0-1.0",
            },
            "rules": [
                "Prefer LLM judgment over rigid keyword rules.",
                "If the answer only uses broad verbs like 负责、推进、协调、优化 without concrete actions, include missing_action or too_generic.",
                "If the answer claims success without evidence, include missing_result or missing_metric.",
                "If the answer claims a result but causality is unclear, include weak_attribution.",
                "For technical roles or technical answers, require constraints, trade-offs, validation, edge cases, and failure handling.",
                "Use sufficient_for_now only when the current competency has enough evidence to move on.",
                "Do not judge personality or background; judge only answer evidence.",
            ],
        },
        ensure_ascii=False,
    )


def parse_answer_gap_response(raw: str) -> AnswerGapAnalysis:
    payload = _parse_json_object(raw)
    gap_types = tuple(
        dict.fromkeys(
            gap
            for gap in (str(item).strip() for item in payload.get("gap_types", []))
            if gap in ANSWER_GAP_TYPES
        )
    )
    if not gap_types:
        gap_types = ("too_generic",)
    evidence_status = {
        str(key): str(value)
        for key, value in dict(payload.get("evidence_status", {})).items()
        if str(value) in {"missing", "mentioned", "partial", "supported", "strong"}
    }
    return AnswerGapAnalysis(
        gap_types=gap_types,
        evidence_status=evidence_status,
        specificity_level=str(payload.get("specificity_level", "unknown")),
        answer_quality_summary=str(payload.get("answer_quality_summary", "")),
        best_next_probe_target=str(payload.get("best_next_probe_target", "")),
        risk_flags=tuple(str(item) for item in payload.get("risk_flags", []) if str(item).strip()),
        confidence=_clamp_float(payload.get("confidence"), 0.0, 1.0, default=0.5),
        raw_response=raw,
    )


def fallback_answer_gap_analysis(*, answer: str, missing_evidence: tuple[str, ...] = ()) -> AnswerGapAnalysis:
    text = answer.strip()
    gaps: list[str] = []
    if len(text) < 30:
        gaps.append("too_generic")
    if _contains_any(text, ("我们", "团队")) and not _contains_any(text, ("我做", "我负责", "我主导", "由我")):
        gaps.append("missing_action")
    if _contains_any(text, ("不错", "很好", "有效", "提升", "优化")) and not any(ch.isdigit() for ch in text):
        gaps.append("missing_metric")
    if _contains_any(text, ("技术", "接口", "系统", "性能", "架构", "代码")):
        gaps.append("missing_technical_depth")
    if missing_evidence and not gaps:
        gaps.append("too_generic")
    if not gaps:
        gaps.append("sufficient_for_now")
    return AnswerGapAnalysis(
        gap_types=tuple(dict.fromkeys(gaps)),
        answer_quality_summary="LLM gap analyzer unavailable; used weak fallback signals.",
        best_next_probe_target=missing_evidence[0] if missing_evidence else "",
        confidence=0.25,
        fallback_used=True,
    )


def _parse_json_object(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Answer gap response must be a JSON object")
    return payload


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _clamp_float(value: Any, min_value: float, max_value: float, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, number))
