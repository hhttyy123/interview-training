from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


InterviewStage = Literal["opening", "early", "middle", "late", "closing", "recovery"]
QuestionStyleId = Literal["open", "clarification", "evidence", "pressure", "relaxed", "reflection", "company_fit"]
InterviewStyleId = Literal["supportive", "standard", "formal", "pressure", "senior", "final_round"]
EvidenceStatus = Literal["missing", "mentioned", "partial", "supported", "strong", "contradictory"]
EvidenceCategory = Literal[
    "context",
    "task",
    "action",
    "decision",
    "tradeoff",
    "collaboration",
    "result",
    "metric",
    "learning",
    "company_fit",
    "role_fit",
    "technical_depth",
    "business_judgment",
    "risk",
]
QuestionShape = Literal[
    "open_expand",
    "clarify_reference",
    "ask_specific_action",
    "ask_metric",
    "ask_tradeoff",
    "ask_counterfactual",
    "challenge_attribution",
    "ask_reflection",
    "connect_company",
    "connect_role",
    "recover_narrow",
]
RoleFamily = Literal[
    "product_business",
    "operations_growth",
    "engineering",
    "data_analytics",
    "design_creative",
    "marketing_brand",
    "sales_customer",
    "consulting_strategy",
    "finance_risk",
    "hr_admin",
    "research_academic",
    "education_training",
    "medical_healthcare",
    "legal_compliance",
    "supply_chain_manufacturing",
    "public_service",
    "general",
]
CompetencyArchetype = Literal[
    "problem_framing",
    "domain_knowledge",
    "execution_delivery",
    "collaboration_influence",
    "analytical_reasoning",
    "technical_depth",
    "customer_user_understanding",
    "commercial_judgment",
    "creative_solution",
    "communication_expression",
    "ownership_resilience",
    "learning_reflection",
    "compliance_risk_awareness",
    "leadership_planning",
]
StrategyCategory = Literal[
    "opening",
    "clarification",
    "evidence_probe",
    "depth_probe",
    "pressure",
    "reflection",
    "role_fit",
    "company_fit",
    "recovery",
]


@dataclass(frozen=True)
class EvidenceQualityBar:
    unacceptable: str
    weak: str
    acceptable: str
    strong: str


@dataclass(frozen=True)
class EvidenceRef:
    turn_index: int
    source: Literal["answer", "resume", "company_card", "jd"]
    excerpt: str
    interpreted_as: str
    confidence: float = 0.5


@dataclass
class EvidenceSlot:
    id: str
    competency_id: str
    label: str
    category: EvidenceCategory
    required: bool = True
    priority: int = 50
    status: EvidenceStatus = "missing"
    confidence: float = 0.0
    refs: list[EvidenceRef] = field(default_factory=list)
    last_asked_turn: int | None = None
    ask_count: int = 0
    quality_bar: EvidenceQualityBar | None = None


@dataclass(frozen=True)
class EvidenceUpdate:
    slot_id: str
    status: EvidenceStatus
    confidence: float
    excerpt: str
    rationale: str
    next_best_probe: str = ""


@dataclass(frozen=True)
class ExpectedEvidence:
    label: str
    category: EvidenceCategory
    quality_hint: str = ""


@dataclass(frozen=True)
class QuestionAnchor:
    source: Literal["last_answer", "resume", "job_model", "company_card", "previous_gap", "interview_stage"]
    summary: str
    quote: str = ""
    turn_index: int | None = None
    confidence: Literal["high", "medium", "low"] = "medium"


@dataclass(frozen=True)
class StrategyCondition:
    type: str
    operator: Literal["eq", "neq", "gt", "lt", "includes", "missing"]
    value: object
    weight: int = 0


@dataclass(frozen=True)
class FollowUpStrategy:
    id: str
    name: str
    category: StrategyCategory
    methodology_ids: tuple[str, ...]
    applicable_stages: tuple[InterviewStage, ...]
    applicable_evidence_categories: tuple[EvidenceCategory, ...]
    question_style_id: QuestionStyleId
    pressure_level: Literal[0, 1, 2, 3] = 0
    preferred_styles: tuple[InterviewStyleId, ...] = ("standard",)
    applicable_role_families: tuple[RoleFamily, ...] = ("general",)
    applicable_competency_archetypes: tuple[CompetencyArchetype, ...] = ()
    trigger_conditions: tuple[StrategyCondition, ...] = ()
    suppress_conditions: tuple[StrategyCondition, ...] = ()
    question_shapes: tuple[QuestionShape, ...] = ("clarify_reference",)
    expected_evidence: tuple[ExpectedEvidence, ...] = ()
    prompt_hints: tuple[str, ...] = ()
    disallowed_moves: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategySelectionResult:
    selected: FollowUpStrategy
    score: float
    score_breakdown: dict[str, float]
    selected_because: str
    alternatives: tuple[tuple[str, float, str], ...] = ()


@dataclass(frozen=True)
class CareerProfile:
    role_title: str
    role_family: RoleFamily = "general"
    seniority: str = "unknown"
    work_mode: str = "unknown"
    core_work_objects: tuple[str, ...] = ()
    typical_tasks: tuple[str, ...] = ()
    common_deliverables: tuple[str, ...] = ()
    success_metrics: tuple[str, ...] = ()
    collaboration_objects: tuple[str, ...] = ()
    risk_types: tuple[str, ...] = ()
    competency_archetypes: tuple[CompetencyArchetype, ...] = ()
    source: Literal["dynamic_jd", "user_input", "role_template", "hybrid"] = "user_input"
    confidence: float = 0.5


@dataclass(frozen=True)
class MethodologyMove:
    name: str
    purpose: str
    when_to_use: str
    question_shapes: tuple[QuestionShape, ...]
    expected_evidence: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()


@dataclass(frozen=True)
class MethodologyCard:
    id: str
    title: str
    source_type: Literal["book_note", "paper", "article", "interview_review", "internal_note", "public_framework"]
    core_principle: str
    applicable_scenarios: tuple[str, ...]
    applicable_role_families: tuple[RoleFamily, ...] = ("general",)
    applicable_competency_archetypes: tuple[CompetencyArchetype, ...] = ()
    interview_moves: tuple[MethodologyMove, ...] = ()
    anti_patterns: tuple[str, ...] = ()
    source_title: str = ""
    source_url: str = ""
    license_note: str = ""


@dataclass(frozen=True)
class QuestionConstraints:
    max_chars: int = 70
    must_reference_anchor: bool = True
    one_question_only: bool = True
    no_scoring: bool = True
    language: str = "zh-CN"


@dataclass(frozen=True)
class QuestionPlan:
    question_id: str
    turn_index: int
    stage: InterviewStage
    competency_id: str
    competency_name: str
    strategy_id: str
    strategy_name: str
    methodology_ids: tuple[str, ...]
    interview_style_id: InterviewStyleId
    question_style_id: QuestionStyleId
    pressure_level: Literal[0, 1, 2, 3]
    anchor: QuestionAnchor
    expected_evidence: tuple[ExpectedEvidence, ...]
    missing_evidence_before_question: tuple[EvidenceSlot, ...]
    covered_evidence_before_question: tuple[EvidenceSlot, ...]
    ask_intent: str
    question_shape: QuestionShape
    constraints: QuestionConstraints = field(default_factory=QuestionConstraints)
    prompt_hints: tuple[str, ...] = ()
    disallowed_moves: tuple[str, ...] = ()
    methodology_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuestionTraceDecision:
    question_id: str
    turn_index: int
    strategy_id: str
    methodology_ids: tuple[str, ...]
    evidence_target_ids: tuple[str, ...]
    selected_because: str
    anchor_summary: str
    alternatives: tuple[tuple[str, float, str], ...] = ()
