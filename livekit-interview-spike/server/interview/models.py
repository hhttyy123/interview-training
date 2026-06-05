from dataclasses import dataclass, field


@dataclass(frozen=True)
class CompanyIntelligenceCard:
    company_name: str
    target_role: str
    summary: str
    business_lines: tuple[str, ...] = ()
    products_or_services: tuple[str, ...] = ()
    market_position: tuple[str, ...] = ()
    financial_strength: tuple[str, ...] = ()
    recent_context: tuple[str, ...] = ()
    culture_and_values: tuple[str, ...] = ()
    role_relevant_points: tuple[str, ...] = ()
    interview_talking_points: tuple[str, ...] = ()
    company_understanding_questions: tuple[str, ...] = ()
    source_notes: tuple[str, ...] = ()
    verification_status: str = "unverified"
    confidence: float = 0.2


@dataclass(frozen=True)
class CompetencyDimension:
    id: str
    name: str
    description: str
    default_weight: float
    observable_signals: tuple[str, ...]
    weak_signals: tuple[str, ...]


@dataclass(frozen=True)
class RoleTemplate:
    id: str
    label: str
    generic_jd: str
    competencies: tuple[CompetencyDimension, ...]
    question_seeds: tuple[str, ...]


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    label: str
    gender: str
    age_style: str
    voice_name: str
    rate: str
    pitch: str
    volume: str
    tone: str
    interviewer_style_prompt: str


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
class DynamicCompetency:
    """AI 动态生成的能力维度 — 替代硬编码 CompetencyDimension。"""
    id: str
    name: str
    description: str
    weight: int
    observable_signals: tuple[str, ...] = ()
    weak_signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class DynamicEvidenceRequirement:
    """AI 动态生成的证据要求 — 替代依赖 observable_signals 拆词的 EvidenceRequirement。"""
    id: str
    name: str
    description: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class DynamicRubricDimension:
    """AI 动态生成的评分维度 — 替代硬编码 RubricDimension。"""
    id: str
    name: str
    description: str
    weak_anchor: str
    normal_anchor: str
    strong_anchor: str


@dataclass(frozen=True)
class DynamicJobModel:
    """AI 动态生成的完整岗位面试模型。

    这是单一对象，承载任意岗位的全部面试配置：
    能力维度、证据要求、评分标准、种子问题、开场白等。
    """
    job_title: str
    job_summary: str
    core_requirements: tuple[str, ...] = ()
    interview_focus: tuple[str, ...] = ()
    competencies: tuple[DynamicCompetency, ...] = ()
    question_seeds: tuple[str, ...] = ()
    competency_weights: dict[str, int] = field(default_factory=dict)
    question_style_weights: dict[str, int] = field(default_factory=dict)
    focus_competency_id: str = ""
    focus_question_style_id: str = "open"
    evidence_requirements: tuple[tuple[str, tuple[DynamicEvidenceRequirement, ...]], ...] = ()
    rubric_dimensions: tuple[DynamicRubricDimension, ...] = ()
    recommended_voice: dict[str, str] = field(default_factory=dict)
    analysis_notes: tuple[str, ...] = ()
    analysis_source: str = "deepseek"
    opening_question: str = ""


@dataclass(frozen=True)
class InterviewTurn:
    question: str
    answer: str
    capability_id: str
    question_style_id: str = "open"


@dataclass
class InterviewState:
    job_name: str = "产品经理"
    job_id: str = "product_manager"
    scenario: str = "项目经历深挖"
    mode_id: str = "standard"
    competency_id: str = "requirement_analysis"
    strategy_id: str = "evidence_probe"
    company_card: CompanyIntelligenceCard | None = None
    jd_text: str = ""
    resume_text: str = ""
    voice_profile_id: str = "gentle_female_young"
    voice_rate: str = ""
    voice_pitch: str = ""
    voice_volume: str = ""
    interviewer_tone: str = "encouraging"
    competency_weights: dict[str, int] = field(default_factory=dict)
    question_style_weights: dict[str, int] = field(default_factory=dict)
    min_candidate_turns: int = 6
    max_candidate_turns: int = 14
    dynamic_model: DynamicJobModel | None = None
    turns: list[InterviewTurn] = field(default_factory=list)
    last_question: str = ""
    current_capability_id: str = "requirement_analysis"
    current_question_style_id: str = "open"

    @property
    def candidate_turn_count(self) -> int:
        return len(self.turns)
