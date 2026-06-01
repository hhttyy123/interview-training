from app.interview.prompt_builder import build_interviewer_prompt


def test_interviewer_prompt_contains_structured_interview_context() -> None:
    prompt = build_interviewer_prompt(
        job_id="product_manager",
        mode_id="standard",
        competency_id="requirement_analysis",
        strategy_id="evidence_probe",
    )

    assert "Structured interview training coach" in prompt
    assert "Target job: Product manager" in prompt
    assert "Competency: Requirement analysis" in prompt
    assert "Strategy: Evidence probe" in prompt
    assert "Rubric anchors for internal judgment" in prompt
    assert "Reply in Chinese." in prompt
    assert "Ask exactly one follow-up question." in prompt
    assert "Do not repeat the same concern for more than two turns." in prompt
    assert "The question should feel like a human interviewer" in prompt
