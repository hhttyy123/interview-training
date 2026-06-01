from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewerRole:
    id: str
    title: str
    mission: str
    boundaries: tuple[str, ...]


@dataclass(frozen=True)
class TrainingMode:
    id: str
    name: str
    behavior: str


@dataclass(frozen=True)
class Competency:
    id: str
    name: str
    definition: str
    observable_signals: tuple[str, ...]
    evidence_required: tuple[str, ...]


@dataclass(frozen=True)
class FollowupStrategy:
    id: str
    name: str
    purpose: str
    when_to_use: str


@dataclass(frozen=True)
class RubricLevel:
    score: int
    anchor: str


@dataclass(frozen=True)
class Rubric:
    competency_id: str
    levels: tuple[RubricLevel, ...]


@dataclass(frozen=True)
class JobProfile:
    id: str
    name: str
    level: str
    core_tasks: tuple[str, ...]
    competency_ids: tuple[str, ...]
