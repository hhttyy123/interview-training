from dataclasses import dataclass, field


@dataclass(frozen=True)
class RubricDimension:
    id: str
    name: str
    description: str
    weak_anchor: str
    normal_anchor: str
    strong_anchor: str


@dataclass(frozen=True)
class EvidenceRequirement:
    id: str
    name: str
    description: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityTrack:
    id: str
    name: str
    description: str
    requirements: tuple[EvidenceRequirement, ...]


@dataclass(frozen=True)
class InterviewTurn:
    question: str
    answer: str
    capability_id: str


@dataclass
class InterviewState:
    job_name: str = "产品经理"
    scenario: str = "项目经历深挖"
    mode_id: str = "standard"
    competency_id: str = "requirement_analysis"
    strategy_id: str = "evidence_probe"
    min_candidate_turns: int = 6
    max_candidate_turns: int = 14
    turns: list[InterviewTurn] = field(default_factory=list)
    last_question: str = ""
    current_capability_id: str = "requirement_analysis"

    @property
    def candidate_turn_count(self) -> int:
        return len(self.turns)
