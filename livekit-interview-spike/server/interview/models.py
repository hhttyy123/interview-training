from dataclasses import dataclass, field


@dataclass(frozen=True)
class RubricDimension:
    id: str
    name: str
    description: str
    weak_anchor: str
    strong_anchor: str


@dataclass(frozen=True)
class InterviewTurn:
    question: str
    answer: str


@dataclass
class InterviewState:
    job_name: str = "产品经理"
    scenario: str = "项目经历深挖"
    mode_id: str = "standard"
    competency_id: str = "requirement_analysis"
    strategy_id: str = "evidence_probe"
    max_candidate_turns: int = 4
    turns: list[InterviewTurn] = field(default_factory=list)
    last_question: str = ""

    @property
    def candidate_turn_count(self) -> int:
        return len(self.turns)

    @property
    def should_finish(self) -> bool:
        return self.candidate_turn_count >= self.max_candidate_turns
