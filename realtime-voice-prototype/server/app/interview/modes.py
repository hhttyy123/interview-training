from app.interview.models import TrainingMode


TRAINING_MODES: dict[str, TrainingMode] = {
    "standard": TrainingMode(
        id="standard",
        name="Standard practice",
        behavior=(
            "Use a professional interviewer tone. Keep pressure moderate. "
            "Prioritize one high-value follow-up question that exposes missing evidence."
        ),
    ),
    "guided": TrainingMode(
        id="guided",
        name="Guided practice",
        behavior=(
            "Be supportive and scaffold the answer. If the candidate is vague, ask a simple "
            "question that helps them recover the missing STAR element."
        ),
    ),
    "challenge": TrainingMode(
        id="challenge",
        name="Challenge practice",
        behavior=(
            "Increase interview pressure. Probe assumptions, trade-offs, ownership, and weak evidence, "
            "while remaining fair and concise."
        ),
    ),
}


def get_training_mode(mode_id: str) -> TrainingMode:
    return TRAINING_MODES.get(mode_id, TRAINING_MODES["standard"])
