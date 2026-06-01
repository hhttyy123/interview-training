from app.interview.models import FollowupStrategy


FOLLOWUP_STRATEGIES: dict[str, FollowupStrategy] = {
    "clarification_probe": FollowupStrategy(
        id="clarification_probe",
        name="Clarification probe",
        purpose="Clarify an ambiguous situation, role, goal, or context.",
        when_to_use="Use when the answer lacks background, scope, target user, or the candidate's role.",
    ),
    "evidence_probe": FollowupStrategy(
        id="evidence_probe",
        name="Evidence probe",
        purpose="Ask for concrete evidence behind a claim or decision.",
        when_to_use="Use when the answer has conclusions but lacks data, examples, validation, or trade-offs.",
    ),
    "result_probe": FollowupStrategy(
        id="result_probe",
        name="Result probe",
        purpose="Force a clearer connection between action and measurable result.",
        when_to_use="Use when the answer describes actions but does not prove outcome or impact.",
    ),
    "reflection_probe": FollowupStrategy(
        id="reflection_probe",
        name="Reflection probe",
        purpose="Test learning ability and judgment after the event.",
        when_to_use="Use after the candidate has described situation, action, and result with enough detail.",
    ),
}


def get_followup_strategy(strategy_id: str) -> FollowupStrategy:
    return FOLLOWUP_STRATEGIES.get(strategy_id, FOLLOWUP_STRATEGIES["evidence_probe"])
