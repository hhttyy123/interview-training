from __future__ import annotations

from interview.followup.models import MethodologyCard, MethodologyMove


DEFAULT_METHODOLOGY_CARDS: tuple[MethodologyCard, ...] = (
    MethodologyCard(
        id="star_behavioral",
        title="STAR behavioral interview",
        source_type="public_framework",
        core_principle="Collect Situation, Task, Action, and Result separately instead of accepting a broad story.",
        applicable_scenarios=("behavioral_interview", "project_experience", "internship_experience"),
        interview_moves=(
            MethodologyMove(
                name="Probe action",
                purpose="Identify the candidate's personal contribution.",
                when_to_use="The answer describes a team outcome but not the candidate's own actions.",
                question_shapes=("ask_specific_action",),
                expected_evidence=("personal role", "concrete action", "decision ownership"),
            ),
            MethodologyMove(
                name="Probe result",
                purpose="Validate the outcome with observable evidence.",
                when_to_use="The answer claims success without metrics or feedback.",
                question_shapes=("ask_metric",),
                expected_evidence=("metric", "feedback", "before-after comparison"),
            ),
        ),
        anti_patterns=("Do not ask all STAR parts in one long question.",),
    ),
    MethodologyCard(
        id="funnel_probe",
        title="Funnel follow-up interview",
        source_type="internal_note",
        core_principle="Move from broad clarification to concrete evidence, then depth or challenge when needed.",
        applicable_scenarios=("real_time_voice_interview", "unclear_answer", "multi_turn_followup"),
        interview_moves=(
            MethodologyMove(
                name="Clarify reference",
                purpose="Resolve vague wording before judging ability.",
                when_to_use="The answer contains vague phrases or unclear references.",
                question_shapes=("clarify_reference",),
            ),
            MethodologyMove(
                name="Narrow recovery",
                purpose="Help the candidate continue when the answer is too short or stuck.",
                when_to_use="The candidate gives a very short answer or appears stuck.",
                question_shapes=("recover_narrow",),
            ),
        ),
        anti_patterns=("Do not challenge before the basic context is clear.",),
    ),
    MethodologyCard(
        id="bar_raiser_challenge",
        title="Evidence challenge interview",
        source_type="internal_note",
        core_principle="Challenge attribution, boundaries, and data quality without attacking the candidate.",
        applicable_scenarios=("pressure_interview", "result_claim", "logic_gap"),
        interview_moves=(
            MethodologyMove(
                name="Challenge attribution",
                purpose="Check whether the claimed result can be linked to the candidate's action.",
                when_to_use="The answer claims impact but does not explain attribution.",
                question_shapes=("challenge_attribution",),
                expected_evidence=("causal link", "comparison", "candidate action"),
                risks=("Do not imply dishonesty; challenge the evidence, not the person."),
            ),
            MethodologyMove(
                name="Counterfactual probe",
                purpose="Test whether the candidate understands boundary conditions.",
                when_to_use="The answer presents one solution without tradeoffs or alternatives.",
                question_shapes=("ask_counterfactual",),
            ),
        ),
        anti_patterns=("Do not use insulting or dismissive language.",),
    ),
    MethodologyCard(
        id="reflection_learning",
        title="Reflection and learning probe",
        source_type="internal_note",
        core_principle="After core evidence is collected, test learning, transferability, and maturity.",
        applicable_scenarios=("late_stage_interview", "complete_story", "growth_potential"),
        interview_moves=(
            MethodologyMove(
                name="Redo decision",
                purpose="Reveal learning quality and decision maturity.",
                when_to_use="The candidate has described a complete experience.",
                question_shapes=("ask_reflection",),
                expected_evidence=("lesson", "changed decision", "transferable principle"),
            ),
        ),
        anti_patterns=("Do not ask reflection before the base event is understood.",),
    ),
)


def get_methodology_card(card_id: str) -> MethodologyCard | None:
    return next((card for card in DEFAULT_METHODOLOGY_CARDS if card.id == card_id), None)
