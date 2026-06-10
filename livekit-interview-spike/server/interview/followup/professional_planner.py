from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass

from interview.followup.answer_gap_analyzer import (
    AnswerGapAnalysis,
    CompletionProvider,
    analyze_answer_gap_with_llm,
    fallback_answer_gap_analysis,
)
from interview.followup.models import (
    EvidenceSlot,
    QuestionAnchor,
    QuestionConstraints,
    QuestionPlan,
)
from interview.followup.prompt_renderer import render_question_plan_prompt
from interview.followup.rag.embeddings import embedding_provider_from_env
from interview.followup.rag.models import RetrievalQuery, RetrievalResult
from interview.followup.rag.qdrant_store import qdrant_store_from_env
from interview.followup.rag.retriever import MethodologyRetriever
from interview.followup.strategy_cards import StrategyCard, StrategyCardSelection, select_strategy_card
from interview.models import CapabilityTrack, InterviewTurn
from runtime_flags import pro_followup_rag_enabled


@dataclass(frozen=True)
class ProfessionalFollowupResult:
    prompt: str
    plan: QuestionPlan
    gap: AnswerGapAnalysis
    strategy_selection: StrategyCardSelection
    rag_results: tuple[RetrievalResult, ...]
    event_payload: dict[str, object]


@dataclass(frozen=True)
class RagAttempt:
    results: list[RetrievalResult]
    raw_count: int = 0
    filtered_count: int = 0
    min_score: float = 0.0
    timeout_ms: int = 0
    embedding_ms: int = 0
    search_ms: int = 0
    rerank_ms: int = 0
    cache_hit: bool = False
    error: str = ""


_RETRIEVER: MethodologyRetriever | None = None
_RAG_CACHE: dict[str, tuple[float, list[RetrievalResult], int]] = {}


async def build_professional_followup(
    *,
    role_name: str,
    current_track: CapabilityTrack,
    question_style_id: str,
    interview_style_id: str,
    turns: list[InterviewTurn],
    missing_evidence: tuple[str, ...],
    recent_strategy_ids: tuple[str, ...] = (),
    provider: CompletionProvider,
    rag_limit: int | None = None,
    enable_rag: bool = True,
) -> ProfessionalFollowupResult:
    if not turns:
        raise ValueError("Professional follow-up requires at least one candidate turn")

    started_at = time.perf_counter()
    last_turn = turns[-1]
    gap_started_at = time.perf_counter()
    gap = await _analyze_gap(
        provider=provider,
        role_name=role_name,
        competency_name=current_track.name,
        question_style_id=question_style_id,
        previous_question=last_turn.question,
        answer=last_turn.answer,
        missing_evidence=missing_evidence,
        recent_turns=tuple((turn.question, turn.answer) for turn in turns[-3:]),
    )
    gap_latency_ms = _elapsed_ms(gap_started_at)
    evidence_categories = _evidence_categories_from_gap(gap)
    competency_archetypes = _competency_archetypes_from_track(current_track)
    role_family = _role_family_from_role_name(role_name)
    selection = select_strategy_card(
        gap_types=gap.gap_types,
        question_style_id=question_style_id,
        interview_style_id=interview_style_id,
        role_family=role_family,
        competency_archetypes=competency_archetypes,
        evidence_categories=evidence_categories,
        recent_strategy_ids=recent_strategy_ids,
    )
    rag_query = _build_retrieval_query(
        gap=gap,
        card=selection.card,
        role_name=role_name,
        competency_name=current_track.name,
        role_family=role_family,
        competency_archetypes=competency_archetypes,
        evidence_categories=evidence_categories,
        limit=rag_limit or int(os.getenv("PRO_FOLLOWUP_RAG_LIMIT", os.getenv("RAG_RETRIEVAL_LIMIT", "4"))),
    )
    rag_started_at = time.perf_counter()
    rag_attempt = await _retrieve_methodology(query=rag_query, enabled=enable_rag)
    rag_results = rag_attempt.results
    rag_latency_ms = _elapsed_ms(rag_started_at)
    plan = _build_plan(
        role_name=role_name,
        current_track=current_track,
        question_style_id=question_style_id,
        interview_style_id=interview_style_id,
        turn_index=len(turns) + 1,
        last_turn=last_turn,
        missing_evidence=missing_evidence,
        evidence_categories=evidence_categories,
        selection=selection,
        gap=gap,
        rag_results=rag_results,
    )
    prompt = render_question_plan_prompt(plan)
    return ProfessionalFollowupResult(
        prompt=prompt,
        plan=plan,
        gap=gap,
        strategy_selection=selection,
        rag_results=tuple(rag_results),
        event_payload=_event_payload(
            plan=plan,
            gap=gap,
            selection=selection,
            rag_results=rag_results,
            rag_query=rag_query,
            rag_attempt=rag_attempt,
            timings={
                "gapMs": gap_latency_ms,
                "ragMs": rag_latency_ms,
                "totalMs": _elapsed_ms(started_at),
            },
        ),
    )


async def _analyze_gap(
    *,
    provider: CompletionProvider,
    role_name: str,
    competency_name: str,
    question_style_id: str,
    previous_question: str,
    answer: str,
    missing_evidence: tuple[str, ...],
    recent_turns: tuple[tuple[str, str], ...],
) -> AnswerGapAnalysis:
    timeout = float(os.getenv("PRO_FOLLOWUP_LLM_TIMEOUT_SECONDS", "8"))
    try:
        return await asyncio.wait_for(
            analyze_answer_gap_with_llm(
                provider=provider,
                role_name=role_name,
                competency_name=competency_name,
                question_style_id=question_style_id,
                previous_question=previous_question,
                answer=answer,
                missing_evidence=missing_evidence,
                recent_turns=recent_turns,
            ),
            timeout=timeout,
        )
    except Exception:
        return fallback_answer_gap_analysis(answer=answer, missing_evidence=missing_evidence)


def _build_retrieval_query(
    *,
    gap: AnswerGapAnalysis,
    card: StrategyCard,
    role_name: str,
    competency_name: str,
    role_family: str,
    competency_archetypes: tuple[str, ...],
    evidence_categories: tuple[str, ...],
    limit: int,
) -> RetrievalQuery:
    return RetrievalQuery(
        query_text=_rag_query_text(gap=gap, card=card, role_name=role_name, competency_name=competency_name),
        limit=limit,
        strategy_category=_rag_strategy_category(card),
        role_family="general",
        competency_archetypes=competency_archetypes,
        evidence_categories=evidence_categories,
    )


async def _retrieve_methodology(*, query: RetrievalQuery, enabled: bool = True) -> RagAttempt:
    if not enabled:
        return RagAttempt(results=[], error="RAG disabled by followup mode")
    if not _rag_enabled():
        return RagAttempt(results=[], error="RAG disabled by PRO_FOLLOWUP_RAG_ENABLED")
    timeout = float(os.getenv("PRO_FOLLOWUP_RAG_TIMEOUT_SECONDS", "12"))
    min_score = float(os.getenv("PRO_FOLLOWUP_RAG_MIN_SCORE", "0.42"))
    cache_key = _rag_cache_key(query=query, min_score=min_score)
    cached = _get_cached_rag(cache_key)
    if cached is not None:
        return RagAttempt(
            results=cached[0],
            raw_count=cached[1],
            filtered_count=len(cached[0]),
            min_score=min_score,
            timeout_ms=int(timeout * 1000),
            cache_hit=True,
        )
    try:
        trace = await asyncio.wait_for(_retriever().retrieve_with_trace(query), timeout=timeout)
    except Exception as error:
        return RagAttempt(
            results=[],
            min_score=min_score,
            timeout_ms=int(timeout * 1000),
            error=f"{type(error).__name__}: {error}",
        )
    results = trace.results
    filtered = [result for result in results if result.score >= min_score]
    _set_cached_rag(cache_key, filtered, raw_count=len(results))
    return RagAttempt(
        results=filtered,
        raw_count=len(results),
        filtered_count=len(filtered),
        min_score=min_score,
        timeout_ms=int(timeout * 1000),
        embedding_ms=trace.embedding_ms,
        search_ms=trace.search_ms,
        rerank_ms=trace.rerank_ms,
    )


def _rag_enabled() -> bool:
    return pro_followup_rag_enabled()


def _retriever() -> MethodologyRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = MethodologyRetriever(
            embedding_provider=embedding_provider_from_env(),
            vector_store=qdrant_store_from_env(),
        )
    return _RETRIEVER


def _rag_cache_key(*, query: RetrievalQuery, min_score: float) -> str:
    return json.dumps(
        {
            "text": query.query_text,
            "limit": query.limit,
            "strategy_category": query.strategy_category,
            "role_family": query.role_family,
            "competency_archetypes": list(query.competency_archetypes),
            "evidence_categories": list(query.evidence_categories),
            "min_score": min_score,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _get_cached_rag(cache_key: str) -> tuple[list[RetrievalResult], int] | None:
    item = _RAG_CACHE.get(cache_key)
    if item is None:
        return None
    created_at, results, raw_count = item
    ttl = float(os.getenv("PRO_FOLLOWUP_RAG_CACHE_TTL_SECONDS", "600"))
    if ttl > 0 and time.monotonic() - created_at > ttl:
        _RAG_CACHE.pop(cache_key, None)
        return None
    return results, raw_count


def _set_cached_rag(cache_key: str, results: list[RetrievalResult], *, raw_count: int) -> None:
    max_size = int(os.getenv("PRO_FOLLOWUP_RAG_CACHE_MAX_SIZE", "128"))
    if max_size <= 0:
        return
    if len(_RAG_CACHE) >= max_size:
        oldest_key = min(_RAG_CACHE, key=lambda key: _RAG_CACHE[key][0])
        _RAG_CACHE.pop(oldest_key, None)
    _RAG_CACHE[cache_key] = (time.monotonic(), results, raw_count)


def _build_plan(
    *,
    role_name: str,
    current_track: CapabilityTrack,
    question_style_id: str,
    interview_style_id: str,
    turn_index: int,
    last_turn: InterviewTurn,
    missing_evidence: tuple[str, ...],
    evidence_categories: tuple[str, ...],
    selection: StrategyCardSelection,
    gap: AnswerGapAnalysis,
    rag_results: list[RetrievalResult],
) -> QuestionPlan:
    card = selection.card
    slots = _slots_from_gap(
        competency_id=current_track.id,
        missing_evidence=missing_evidence,
        evidence_categories=evidence_categories,
        gap=gap,
    )
    methodology_notes = tuple(_methodology_note(result) for result in rag_results[:4])
    source_ids = tuple(dict.fromkeys(result.chunk.source_id for result in rag_results if result.chunk.source_id))
    hints = (
        *card.recommended_probe_moves[:4],
        f"Answer gap: {', '.join(gap.gap_types)}.",
        f"Next target: {gap.best_next_probe_target or card.title}.",
        f"Scoring impact: {card.scoring_impact}",
    )
    return QuestionPlan(
        question_id=f"q_{turn_index:03d}",
        turn_index=turn_index,
        stage=_stage_from_turn_index(turn_index),
        competency_id=current_track.id,
        competency_name=current_track.name,
        strategy_id=card.strategy_id,
        strategy_name=card.title,
        methodology_ids=source_ids or tuple(card.source_titles[:3]),
        interview_style_id=_safe_interview_style(interview_style_id),
        question_style_id=_safe_question_style(question_style_id, card),
        pressure_level=2 if card.strategy_category == "pressure" else 0,
        anchor=QuestionAnchor(
            source="last_answer",
            summary=last_turn.answer[:90],
            quote=last_turn.answer[:90],
            turn_index=max(0, turn_index - 1),
            confidence="high" if last_turn.answer.strip() else "low",
        ),
        expected_evidence=(),
        missing_evidence_before_question=tuple(slots),
        covered_evidence_before_question=(),
        ask_intent=f"Use {card.strategy_id} for {role_name}/{current_track.name}: {gap.best_next_probe_target or card.title}.",
        question_shape=_safe_question_shape(card.question_shape),
        constraints=QuestionConstraints(max_chars=70),
        prompt_hints=tuple(hints),
        disallowed_moves=card.disallowed_moves or ("Do not score or explain.",),
        methodology_notes=methodology_notes,
    )


def _slots_from_gap(
    *,
    competency_id: str,
    missing_evidence: tuple[str, ...],
    evidence_categories: tuple[str, ...],
    gap: AnswerGapAnalysis,
) -> list[EvidenceSlot]:
    labels = list(missing_evidence[:4])
    if gap.best_next_probe_target:
        labels.insert(0, gap.best_next_probe_target)
    if not labels:
        labels = [f"Collect evidence for {gap_type}" for gap_type in gap.gap_types[:3]]
    categories = evidence_categories or ("action",)
    slots: list[EvidenceSlot] = []
    for index, label in enumerate(dict.fromkeys(labels)):
        category = categories[min(index, len(categories) - 1)]
        status = gap.evidence_status.get(category, "missing")
        if status not in {"missing", "mentioned", "partial", "supported", "strong"}:
            status = "missing"
        slots.append(
            EvidenceSlot(
                id=f"{competency_id}.{category}.{index}",
                competency_id=competency_id,
                label=label,
                category=category,  # type: ignore[arg-type]
                priority=max(35, 90 - index * 8),
                status=status,  # type: ignore[arg-type]
                confidence=gap.confidence,
            )
        )
    return slots


def _event_payload(
    *,
    plan: QuestionPlan,
    gap: AnswerGapAnalysis,
    selection: StrategyCardSelection,
    rag_results: list[RetrievalResult],
    rag_query: RetrievalQuery,
    rag_attempt: RagAttempt,
    timings: dict[str, int],
) -> dict[str, object]:
    return {
        "plannerMode": "professional",
        "plannerTimings": timings,
        "answerGapTypes": list(gap.gap_types),
        "answerGapConfidence": round(gap.confidence, 3),
        "answerGapFallback": gap.fallback_used,
        "answerQualitySummary": gap.answer_quality_summary,
        "bestNextProbeTarget": gap.best_next_probe_target,
        "selectedStrategyId": selection.card.strategy_id,
        "selectedStrategyTitle": selection.card.title,
        "selectedBecause": selection.selected_because,
        "ragEnabled": _rag_enabled(),
        "ragUsed": bool(rag_results),
        "ragRawCount": rag_attempt.raw_count,
        "ragFilteredCount": rag_attempt.filtered_count,
        "ragMinScore": rag_attempt.min_score,
        "ragTimeoutMs": rag_attempt.timeout_ms,
        "ragEmbeddingMs": rag_attempt.embedding_ms,
        "ragSearchMs": rag_attempt.search_ms,
        "ragRerankMs": rag_attempt.rerank_ms,
        "ragCacheHit": rag_attempt.cache_hit,
        "ragError": rag_attempt.error,
        "ragSourceTitles": list(dict.fromkeys(result.chunk.title for result in rag_results[:4])),
        "ragQuery": {
            "text": rag_query.query_text[:900],
            "strategyCategory": rag_query.strategy_category,
            "roleFamily": rag_query.role_family,
            "competencyArchetypes": list(rag_query.competency_archetypes),
            "evidenceCategories": list(rag_query.evidence_categories),
            "limit": rag_query.limit,
        },
        "ragMatches": [
            {
                "title": result.chunk.title,
                "score": round(result.score, 4),
                "ordinal": result.chunk.ordinal,
                "sourceId": result.chunk.source_id,
                "preview": result.chunk.text[:220],
            }
            for result in rag_results[:4]
        ],
        "methodologyIds": list(plan.methodology_ids),
    }


def _rag_query_text(*, gap: AnswerGapAnalysis, card: StrategyCard, role_name: str, competency_name: str) -> str:
    parts = [
        f"role={role_name}",
        f"competency={competency_name}",
        f"answer_gap={','.join(gap.gap_types)}",
        f"strategy={card.strategy_id} {card.title}",
        f"next_probe_target={gap.best_next_probe_target}",
        "recommended_moves=" + "; ".join(card.recommended_probe_moves[:4]),
        "source_focus=" + "; ".join(card.source_titles[:4]),
    ]
    return "\n".join(part for part in parts if part)


def _methodology_note(result: RetrievalResult) -> str:
    chunk = result.chunk
    return f"{chunk.title} (score={result.score:.3f}): {chunk.text[:360]}"


def _evidence_categories_from_gap(gap: AnswerGapAnalysis) -> tuple[str, ...]:
    mapping = {
        "missing_context": "context",
        "missing_task": "task",
        "missing_action": "action",
        "missing_result": "result",
        "missing_metric": "metric",
        "missing_reflection": "learning",
        "missing_tradeoff": "tradeoff",
        "missing_technical_depth": "technical_depth",
        "weak_attribution": "risk",
    }
    categories = [mapping[gap_type] for gap_type in gap.gap_types if gap_type in mapping]
    if "too_generic" in gap.gap_types:
        categories.extend(["context", "action"])
    if not categories:
        categories.append("action")
    return tuple(dict.fromkeys(categories))


def _competency_archetypes_from_track(track: CapabilityTrack) -> tuple[str, ...]:
    text = f"{track.id} {track.name} {track.description}".lower()
    archetypes: list[str] = []
    if any(word in text for word in ("技术", "工程", "系统", "代码", "technical", "engineer")):
        archetypes.append("technical_depth")
    if any(word in text for word in ("分析", "判断", "数据", "analysis", "metric")):
        archetypes.append("analytical_reasoning")
    if any(word in text for word in ("协作", "沟通", "影响", "communication")):
        archetypes.append("collaboration_influence")
    if any(word in text for word in ("交付", "执行", "推进", "delivery")):
        archetypes.append("execution_delivery")
    archetypes.extend(["problem_framing", "execution_delivery", "communication_expression"])
    return tuple(dict.fromkeys(archetypes))[:5]


def _role_family_from_role_name(role_name: str) -> str:
    text = role_name.lower()
    if any(word in text for word in ("工程", "开发", "研发", "算法", "前端", "后端", "engineer", "developer")):
        return "engineering"
    if any(word in text for word in ("数据", "分析", "bi", "analytics")):
        return "data_analytics"
    return "general"


def _rag_strategy_category(card: StrategyCard) -> str:
    if card.strategy_category in {"pressure", "reflection", "clarification", "depth_probe", "evidence_probe"}:
        return {
            "pressure": "structured",
            "reflection": "behavior",
            "clarification": "structured",
            "depth_probe": "technical" if "technical_depth" in card.evidence_categories else "structured",
            "evidence_probe": "behavior",
        }[card.strategy_category]
    return "structured"


def _stage_from_turn_index(turn_index: int):
    if turn_index <= 2:
        return "early"
    if turn_index <= 8:
        return "middle"
    if turn_index <= 13:
        return "late"
    return "closing"


def _safe_interview_style(value: str):
    if value in {"supportive", "standard", "formal", "pressure", "senior", "final_round"}:
        return value
    return "standard"


def _safe_question_style(value: str, card: StrategyCard):
    if value in {"open", "clarification", "evidence", "pressure", "relaxed", "reflection", "company_fit"}:
        return value
    if card.question_style_ids:
        first = card.question_style_ids[0]
        if first in {"open", "clarification", "evidence", "pressure", "relaxed", "reflection", "company_fit"}:
            return first
    return "evidence"


def _safe_question_shape(value: str):
    allowed = {
        "open_expand",
        "clarify_reference",
        "ask_specific_action",
        "ask_metric",
        "ask_tradeoff",
        "ask_counterfactual",
        "challenge_attribution",
        "ask_reflection",
        "connect_company",
        "connect_role",
        "recover_narrow",
    }
    return value if value in allowed else "clarify_reference"


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)
