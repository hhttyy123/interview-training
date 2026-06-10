from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from interview.followup.models import CompetencyArchetype, EvidenceCategory, RoleFamily


AnswerGapType = str


@dataclass(frozen=True)
class StrategyCard:
    strategy_id: str
    title: str
    answer_gap_types: tuple[AnswerGapType, ...]
    strategy_category: str
    question_style_ids: tuple[str, ...]
    interview_style_ids: tuple[str, ...]
    role_families: tuple[RoleFamily | str, ...]
    competency_archetypes: tuple[CompetencyArchetype | str, ...]
    evidence_categories: tuple[EvidenceCategory | str, ...]
    question_shape: str
    trigger_signals: tuple[str, ...]
    recommended_probe_moves: tuple[str, ...]
    disallowed_moves: tuple[str, ...]
    scoring_impact: str
    source_titles: tuple[str, ...]
    priority: int = 50


@dataclass(frozen=True)
class StrategyCardSelection:
    card: StrategyCard
    score: float
    selected_because: str
    alternatives: tuple[tuple[str, float, str], ...] = ()


def default_strategy_card_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "followup_strategy_cards.jsonl"


@lru_cache(maxsize=4)
def load_strategy_cards(path: str | None = None) -> tuple[StrategyCard, ...]:
    source = Path(path) if path else default_strategy_card_path()
    cards = tuple(_iter_strategy_cards(source))
    if not cards:
        raise RuntimeError(f"No follow-up strategy cards found in {source}")
    return cards


def select_strategy_card(
    *,
    gap_types: tuple[str, ...],
    question_style_id: str,
    interview_style_id: str,
    role_family: str = "general",
    competency_archetypes: tuple[str, ...] = (),
    evidence_categories: tuple[str, ...] = (),
    recent_strategy_ids: tuple[str, ...] = (),
    cards: tuple[StrategyCard, ...] | None = None,
) -> StrategyCardSelection:
    candidates: list[tuple[StrategyCard, float, list[str]]] = []
    for card in cards or load_strategy_cards():
        score, reasons = _score_card(
            card=card,
            gap_types=gap_types,
            question_style_id=question_style_id,
            interview_style_id=interview_style_id,
            role_family=role_family,
            competency_archetypes=competency_archetypes,
            evidence_categories=evidence_categories,
            recent_strategy_ids=recent_strategy_ids,
        )
        if score > 0:
            candidates.append((card, score, reasons))

    if not candidates:
        fallback = max(cards or load_strategy_cards(), key=lambda item: item.priority)
        return StrategyCardSelection(
            card=fallback,
            score=1.0,
            selected_because="No strategy card matched; using highest-priority fallback.",
        )

    candidates.sort(key=lambda item: item[1], reverse=True)
    selected, score, reasons = candidates[0]
    alternatives = tuple(
        (card.strategy_id, alt_score, ", ".join(alt_reasons[:3]))
        for card, alt_score, alt_reasons in candidates[1:4]
    )
    return StrategyCardSelection(
        card=selected,
        score=score,
        selected_because=", ".join(reasons[:4]) or "highest scored strategy card",
        alternatives=alternatives,
    )


def _iter_strategy_cards(path: Path) -> Iterable[StrategyCard]:
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            try:
                yield StrategyCard(
                    strategy_id=str(payload["strategy_id"]),
                    title=str(payload["title"]),
                    answer_gap_types=tuple(_strings(payload.get("answer_gap_types"))),
                    strategy_category=str(payload.get("strategy_category", "evidence_probe")),
                    question_style_ids=tuple(_strings(payload.get("question_style_ids"))),
                    interview_style_ids=tuple(_strings(payload.get("interview_style_ids"))),
                    role_families=tuple(_strings(payload.get("role_families")) or ["general"]),
                    competency_archetypes=tuple(_strings(payload.get("competency_archetypes"))),
                    evidence_categories=tuple(_strings(payload.get("evidence_categories"))),
                    question_shape=str(payload.get("question_shape", "clarify_reference")),
                    trigger_signals=tuple(_strings(payload.get("trigger_signals"))),
                    recommended_probe_moves=tuple(_strings(payload.get("recommended_probe_moves"))),
                    disallowed_moves=tuple(_strings(payload.get("disallowed_moves"))),
                    scoring_impact=str(payload.get("scoring_impact", "")),
                    source_titles=tuple(_strings(payload.get("source_titles"))),
                    priority=int(payload.get("priority", 50)),
                )
            except KeyError as exc:
                raise ValueError(f"Missing required field {exc} in {path}:{line_number}") from exc


def _score_card(
    *,
    card: StrategyCard,
    gap_types: tuple[str, ...],
    question_style_id: str,
    interview_style_id: str,
    role_family: str,
    competency_archetypes: tuple[str, ...],
    evidence_categories: tuple[str, ...],
    recent_strategy_ids: tuple[str, ...],
) -> tuple[float, list[str]]:
    score = float(card.priority) / 10
    reasons = [f"priority={card.priority}"]

    gap_overlap = _overlap(gap_types, card.answer_gap_types)
    if gap_overlap:
        score += 55 + gap_overlap * 8
        score += 25 * (gap_overlap / max(1, len(card.answer_gap_types)))
        reasons.append(f"gap_match={gap_overlap}")
    elif "sufficient_for_now" in gap_types and "sufficient_for_now" in card.answer_gap_types:
        score += 30
        reasons.append("sufficient_for_now")
    else:
        score -= 25

    if question_style_id in card.question_style_ids:
        score += 18
        reasons.append(f"question_style={question_style_id}")
    elif question_style_id == "pressure" and card.strategy_category == "pressure":
        score += 12
        reasons.append("pressure_style")

    if interview_style_id in card.interview_style_ids:
        score += 10
        reasons.append(f"interview_style={interview_style_id}")

    if role_family in card.role_families or "general" in card.role_families:
        score += 8
        reasons.append(f"role_family={role_family}")

    archetype_overlap = _overlap(competency_archetypes, card.competency_archetypes)
    if archetype_overlap:
        score += min(15, archetype_overlap * 5)
        reasons.append(f"archetype_match={archetype_overlap}")

    evidence_overlap = _overlap(evidence_categories, card.evidence_categories)
    if evidence_overlap:
        score += min(18, evidence_overlap * 6)
        reasons.append(f"evidence_match={evidence_overlap}")

    repetition_count = recent_strategy_ids.count(card.strategy_id)
    if repetition_count:
        score -= 20 * repetition_count
        reasons.append(f"repetition_penalty={repetition_count}")
    if recent_strategy_ids[-1:] == (card.strategy_id,):
        score -= 25
        reasons.append("last_strategy_penalty")

    if question_style_id == "pressure" and card.strategy_category != "pressure":
        score -= 25
        reasons.append("pressure_category_penalty")
    if question_style_id == "pressure" and card.strategy_category == "pressure":
        score += 24
        reasons.append("pressure_category_match")
    if question_style_id != "pressure" and card.strategy_category == "pressure":
        score -= 12

    return score, reasons


def _overlap(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    return len(set(left).intersection(str(item) for item in right))


def _strings(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [item.strip() for item in value.split() if item.strip()]
    return []
