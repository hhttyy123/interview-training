from __future__ import annotations

from interview.followup.methodology import get_methodology_card
from interview.followup.models import QuestionPlan


def render_question_plan_prompt(plan: QuestionPlan) -> str:
    methodology_lines = []
    for card_id in plan.methodology_ids:
        card = get_methodology_card(card_id)
        if not card:
            continue
        methodology_lines.append(f"- {card.title}: {card.core_principle}")

    missing = ", ".join(slot.label for slot in plan.missing_evidence_before_question[:5]) or "no explicit gap"
    expected = ", ".join(item.label for item in plan.expected_evidence) or "stronger role evidence"
    hints = "\n".join(f"- {hint}" for hint in plan.prompt_hints) or "- Ask a focused follow-up."
    disallowed = "\n".join(f"- {item}" for item in plan.disallowed_moves) or "- Do not score or explain."

    return f"""
You are a real-time Chinese interview coach. Generate exactly one follow-up question.

QuestionPlan:
- questionId: {plan.question_id}
- stage: {plan.stage}
- competency: {plan.competency_name}
- strategy: {plan.strategy_id} / {plan.strategy_name}
- questionStyle: {plan.question_style_id}
- interviewStyle: {plan.interview_style_id}
- pressureLevel: {plan.pressure_level}
- questionShape: {plan.question_shape}
- anchorSource: {plan.anchor.source}
- anchor: {plan.anchor.summary}
- askIntent: {plan.ask_intent}
- missingEvidence: {missing}
- expectedEvidence: {expected}

Methodology:
{chr(10).join(methodology_lines) or "- Internal follow-up heuristic."}

Retrieved methodology notes:
{chr(10).join(f"- {note}" for note in plan.methodology_notes) or "- No external methodology retrieved."}

Prompt hints:
{hints}

Disallowed moves:
{disallowed}

Constraints:
- Output only one Chinese question.
- No markdown, no analysis, no score.
- Keep it under {plan.constraints.max_chars} Chinese characters when possible.
- Must point to the anchor if anchor confidence is not low.
""".strip()
