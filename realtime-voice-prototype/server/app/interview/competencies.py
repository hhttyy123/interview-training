from app.interview.models import Competency, JobProfile


COMPETENCIES: dict[str, Competency] = {
    "requirement_analysis": Competency(
        id="requirement_analysis",
        name="Requirement analysis",
        definition=(
            "Ability to identify real user problems, connect them with business goals, "
            "and justify product decisions with evidence."
        ),
        observable_signals=(
            "Separates user requests from underlying user problems.",
            "Explains prioritization criteria and trade-offs.",
            "Uses data, research, feedback, or scenarios as evidence.",
            "Connects product choices with measurable outcomes.",
        ),
        evidence_required=(
            "Demand source",
            "User problem",
            "Business goal",
            "Decision criteria",
            "Validation method",
            "Result",
        ),
    ),
    "project_delivery": Competency(
        id="project_delivery",
        name="Project delivery",
        definition=(
            "Ability to clarify personal ownership, coordinate stakeholders, manage constraints, "
            "and deliver a visible result."
        ),
        observable_signals=(
            "Clarifies the candidate's own role and decisions.",
            "Explains collaboration across functions.",
            "Describes how risks, delays, or conflicts were handled.",
            "States concrete delivery outcomes and lessons learned.",
        ),
        evidence_required=(
            "Personal responsibility",
            "Stakeholders",
            "Key conflict or constraint",
            "Action taken",
            "Delivery result",
            "Reflection",
        ),
    ),
    "impact_expression": Competency(
        id="impact_expression",
        name="Impact expression",
        definition=(
            "Ability to communicate work results with clear structure, measurable impact, "
            "and honest attribution."
        ),
        observable_signals=(
            "Uses a clear answer structure.",
            "Quantifies before-and-after impact when possible.",
            "Distinguishes team result from personal contribution.",
            "Explains what changed because of the candidate's action.",
        ),
        evidence_required=(
            "Baseline",
            "Metric",
            "Candidate action",
            "Outcome",
            "Attribution",
        ),
    ),
}


JOB_PROFILES: dict[str, JobProfile] = {
    "product_manager": JobProfile(
        id="product_manager",
        name="Product manager",
        level="junior_to_mid",
        core_tasks=(
            "Requirement analysis",
            "Product planning",
            "Cross-functional delivery",
            "Data-informed iteration",
            "Project result communication",
        ),
        competency_ids=(
            "requirement_analysis",
            "project_delivery",
            "impact_expression",
        ),
    )
}


def get_job_profile(job_id: str) -> JobProfile:
    return JOB_PROFILES.get(job_id, JOB_PROFILES["product_manager"])


def get_competency(competency_id: str) -> Competency:
    return COMPETENCIES.get(competency_id, COMPETENCIES["requirement_analysis"])
