from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from interview.followup.professional_planner import ProfessionalFollowupResult, build_professional_followup
from interview.orchestrator import InterviewOrchestrator
from local_providers import DeepSeekStreamingTextProvider


logger = logging.getLogger("interview_spike.followup")


@dataclass(frozen=True)
class FollowupRuntimeResult:
    system_prompt: str
    planner_payload: dict[str, object]
    professional_result: ProfessionalFollowupResult | None = None
    fallback_used: bool = False
    error: str = ""


async def build_followup_runtime_prompt(
    *,
    orchestrator: InterviewOrchestrator,
    llm_provider: DeepSeekStreamingTextProvider,
) -> FollowupRuntimeResult:
    followup_mode = _mode(orchestrator.state.followup_mode)
    if followup_mode == "fast" or not _enabled():
        return FollowupRuntimeResult(
            system_prompt=orchestrator.build_followup_prompt(),
            planner_payload={
                "plannerMode": "fast",
                "followupMode": followup_mode,
                "professionalEnabled": False,
                "ragEnabled": False,
            },
            fallback_used=True,
        )
    try:
        result = await build_professional_followup(
            role_name=orchestrator.state.job_name,
            current_track=orchestrator.current_track(),
            question_style_id=orchestrator.state.current_question_style_id or "open",
            interview_style_id=orchestrator.current_interview_style_id(),
            turns=orchestrator.turns,
            missing_evidence=orchestrator.current_missing_evidence(),
            recent_strategy_ids=tuple(orchestrator.state.recent_strategy_ids),
            provider=llm_provider,
            enable_rag=followup_mode == "professional",
        )
        logger.info(
            "professional_followup planner=professional gaps=%s strategy=%s rag_used=%s rag_sources=%s timings=%s",
            result.event_payload.get("answerGapTypes"),
            result.event_payload.get("selectedStrategyId"),
            result.event_payload.get("ragUsed"),
            result.event_payload.get("ragSourceTitles"),
            result.event_payload.get("plannerTimings"),
        )
        return FollowupRuntimeResult(
            system_prompt=result.prompt,
            planner_payload={
                "plannerMode": "professional",
                "followupMode": followup_mode,
                "professionalEnabled": True,
                **result.event_payload,
            },
            professional_result=result,
        )
    except Exception as error:
        logger.exception("professional follow-up planner failed; falling back to legacy prompt")
        if not _fallback_enabled():
            raise
        return FollowupRuntimeResult(
            system_prompt=orchestrator.build_followup_prompt(),
            planner_payload={
                "plannerMode": "legacy_fallback",
                "followupMode": followup_mode,
                "professionalEnabled": True,
                "plannerError": str(error),
            },
            fallback_used=True,
            error=str(error),
        )


def _enabled() -> bool:
    return os.getenv("PRO_FOLLOWUP_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _mode(raw: str) -> str:
    value = (raw or "fast").strip().lower()
    if value in {"fast", "balanced", "professional"}:
        return value
    return "fast"


def _fallback_enabled() -> bool:
    return os.getenv("PRO_FOLLOWUP_FALLBACK_TO_LEGACY", "true").strip().lower() not in {"0", "false", "no", "off"}
