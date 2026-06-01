from app.interview.models import Rubric, RubricLevel


RUBRICS: dict[str, Rubric] = {
    "requirement_analysis": Rubric(
        competency_id="requirement_analysis",
        levels=(
            RubricLevel(score=1, anchor="Only describes tasks, with no clear user problem or decision basis."),
            RubricLevel(score=3, anchor="Explains problem, goal, and basic reasoning, but evidence is incomplete."),
            RubricLevel(
                score=5,
                anchor=(
                    "Clearly connects user problem, business goal, prioritization criteria, "
                    "validation method, and measurable result."
                ),
            ),
        ),
    ),
    "project_delivery": Rubric(
        competency_id="project_delivery",
        levels=(
            RubricLevel(score=1, anchor="Mentions project work but personal ownership is unclear."),
            RubricLevel(score=3, anchor="States role, stakeholders, and actions, but risk handling or results are vague."),
            RubricLevel(score=5, anchor="Shows clear ownership, coordination, constraint handling, delivery result, and reflection."),
        ),
    ),
    "impact_expression": Rubric(
        competency_id="impact_expression",
        levels=(
            RubricLevel(score=1, anchor="Uses generic positive claims without measurable result."),
            RubricLevel(score=3, anchor="Has structure and some result evidence, but attribution or metrics are incomplete."),
            RubricLevel(score=5, anchor="Communicates structure, baseline, metric change, personal contribution, and business impact."),
        ),
    ),
}


def get_rubric(competency_id: str) -> Rubric:
    return RUBRICS.get(competency_id, RUBRICS["requirement_analysis"])
