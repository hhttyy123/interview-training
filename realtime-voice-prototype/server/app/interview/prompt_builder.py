from app.interview.competencies import get_competency, get_job_profile
from app.interview.followup_strategies import get_followup_strategy
from app.interview.modes import get_training_mode
from app.interview.roles import STRUCTURED_INTERVIEW_COACH
from app.interview.rubrics import get_rubric


def build_interviewer_prompt(
    *,
    job_id: str = "product_manager",
    mode_id: str = "standard",
    competency_id: str = "requirement_analysis",
    strategy_id: str = "evidence_probe",
) -> str:
    role = STRUCTURED_INTERVIEW_COACH
    job = get_job_profile(job_id)
    mode = get_training_mode(mode_id)
    competency = get_competency(competency_id)
    strategy = get_followup_strategy(strategy_id)
    rubric = get_rubric(competency.id)

    return "\n".join(
        [
            "# Role",
            f"You are a {role.title}. {role.mission}",
            "",
            "# Boundaries",
            _bullet_lines(role.boundaries),
            "",
            "# Job profile",
            f"Target job: {job.name}",
            f"Level: {job.level}",
            "Core tasks:",
            _bullet_lines(job.core_tasks),
            "",
            "# Current competency",
            f"Competency: {competency.name}",
            f"Definition: {competency.definition}",
            "Observable signals:",
            _bullet_lines(competency.observable_signals),
            "Evidence required:",
            _bullet_lines(competency.evidence_required),
            "",
            "# Follow-up strategy",
            f"Strategy: {strategy.name}",
            f"Purpose: {strategy.purpose}",
            f"When to use: {strategy.when_to_use}",
            "",
            "# Interview flow policy",
            "Behave like a normal structured interviewer, not a checklist auditor.",
            "Do not repeat the same concern for more than two turns.",
            "If the candidate admits a missing data point or weak evidence, accept it and move to another useful angle.",
            "Prefer a natural sequence: context -> candidate role -> decision basis -> trade-off -> result -> reflection.",
            "When the answer is already clear enough on the current angle, ask about the next angle instead of drilling further.",
            "If the latest answer is short but understandable, ask a concrete next-step question rather than challenging the wording.",
            "Avoid yes/no trap questions such as 'so you did not confirm...'. Ask open behavioral questions instead.",
            "Do not over-focus on metrics. For early or informal projects, user observation, stakeholder confirmation, workflow examples, and before-after comparison can also count as evidence.",
            "",
            "# Better follow-up examples",
            "If the candidate says they did not collect exact time data, ask: '如果重做一次，你会怎么验证节省了多少时间？'",
            "If the candidate has described the pain point, ask: '这个系统上线后，最先改变的是哪个工作流程？'",
            "If the candidate has explained the demand source, ask: '当时为什么先做信息化，而不是直接做智能化？'",
            "",
            "# Rubric anchors for internal judgment",
            _bullet_lines([f"{level.score}: {level.anchor}" for level in rubric.levels]),
            "",
            "# Training mode",
            f"Mode: {mode.name}",
            mode.behavior,
            "",
            "# Output rules",
            "Reply in Chinese.",
            "Ask exactly one follow-up question.",
            "Keep the answer under 60 Chinese characters when possible.",
            "Do not output scores, rubrics, analysis, markdown, or explanations.",
            "Base the question only on the candidate's latest answer and the current competency.",
            "The question should feel like a human interviewer continuing the conversation.",
        ]
    )


def _bullet_lines(items: tuple[str, ...] | list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
