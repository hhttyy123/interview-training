from __future__ import annotations

from dataclasses import replace

from interview.followup.models import CareerProfile, QuestionPlan
from interview.followup.rag.models import RetrievalQuery, RetrievalResult
from interview.followup.rag.retriever import MethodologyRetriever


async def enrich_question_plan_with_rag(
    *,
    plan: QuestionPlan,
    retriever: MethodologyRetriever,
    career_profile: CareerProfile | None = None,
    limit: int = 6,
) -> QuestionPlan:
    query = build_retrieval_query_from_plan(plan=plan, career_profile=career_profile, limit=limit)
    results = await retriever.retrieve(query)
    return attach_methodology_results(plan=plan, results=results)


def build_retrieval_query_from_plan(
    *,
    plan: QuestionPlan,
    career_profile: CareerProfile | None = None,
    limit: int = 6,
) -> RetrievalQuery:
    missing_categories = tuple(
        dict.fromkeys(slot.category for slot in plan.missing_evidence_before_question[:8])
    )
    query_text = "\n".join(
        part
        for part in (
            f"strategy={plan.strategy_id} {plan.strategy_name}",
            f"competency={plan.competency_name}",
            f"ask_intent={plan.ask_intent}",
            f"anchor={plan.anchor.summary}",
            f"question_shape={plan.question_shape}",
        )
        if part
    )
    return RetrievalQuery(
        query_text=query_text,
        limit=limit,
        strategy_id=plan.strategy_id,
        strategy_category=_strategy_category_from_id(plan.strategy_id),
        question_style_id=plan.question_style_id,
        interview_style_id=plan.interview_style_id,
        role_family=career_profile.role_family if career_profile else "",
        competency_archetypes=career_profile.competency_archetypes if career_profile else (),
        evidence_categories=missing_categories,
    )


def attach_methodology_results(
    *,
    plan: QuestionPlan,
    results: list[RetrievalResult],
    max_notes: int = 4,
) -> QuestionPlan:
    notes = tuple(_result_note(result) for result in results[:max_notes])
    retrieved_ids = tuple(
        result.chunk.source_id
        for result in results
        if result.chunk.source_id and result.chunk.source_id not in plan.methodology_ids
    )
    return replace(
        plan,
        methodology_ids=tuple(dict.fromkeys((*plan.methodology_ids, *retrieved_ids))),
        methodology_notes=tuple(dict.fromkeys((*plan.methodology_notes, *notes))),
    )


def _result_note(result: RetrievalResult) -> str:
    chunk = result.chunk
    source = f" source={chunk.source_url}" if chunk.source_url else ""
    return f"{chunk.title} (score={result.score:.3f}{source}): {chunk.text[:260]}"


def _strategy_category_from_id(strategy_id: str) -> str:
    if "pressure" in strategy_id or "challenge" in strategy_id:
        return "pressure"
    if "reflection" in strategy_id or "redo" in strategy_id or "learning" in strategy_id:
        return "reflection"
    if "company" in strategy_id:
        return "company_fit"
    if "role" in strategy_id or "jd" in strategy_id:
        return "role_fit"
    if "clarify" in strategy_id:
        return "clarification"
    if "recover" in strategy_id:
        return "recovery"
    if "depth" in strategy_id or "tradeoff" in strategy_id or "root" in strategy_id:
        return "depth_probe"
    if "open" in strategy_id:
        return "opening"
    return "evidence_probe"
