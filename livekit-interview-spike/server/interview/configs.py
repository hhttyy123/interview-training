from interview.models import (
    CapabilityTrack,
    CompetencyDimension,
    DynamicCompetency,
    DynamicEvidenceRequirement,
    DynamicJobModel,
    DynamicRubricDimension,
    EvidenceRequirement,
    RoleTemplate,
    RubricDimension,
    VoiceProfile,
)


PRODUCT_MANAGER_OPENING = "你好，我们开始正式模拟面试。请先用一分钟说明你对目标公司和岗位的理解。"

ROLE_TEMPLATES: tuple[RoleTemplate, ...] = (
    RoleTemplate(
        id="product_manager",
        label="产品经理",
        generic_jd="负责用户需求分析、产品方案设计、跨团队推进、上线验证和业务结果复盘。",
        competencies=(
            CompetencyDimension("role_core", "岗位专业力", "掌握产品经理核心方法，包括需求分析、方案设计、优先级和验证闭环。", 24, ("需求来源清楚", "方案逻辑完整", "优先级有依据", "验证闭环"), ("只说接到需求", "方案像想法", "优先级靠感觉", "没有验证")),
            CompetencyDimension("business_understanding", "业务理解", "理解公司业务、用户场景、商业目标和岗位能创造的价值。", 18, ("理解业务目标", "连接公司场景", "知道用户价值", "动机可信"), ("只讲兴趣", "不了解业务", "岗位连接弱", "动机模板化")),
            CompetencyDimension("problem_analysis", "问题分析", "能拆解复杂问题，识别真实用户痛点、约束、取舍和边界。", 18, ("问题定义清楚", "用户痛点具体", "取舍有依据", "边界明确"), ("问题泛泛", "用户模糊", "没有取舍", "边界不清")),
            CompetencyDimension("execution_delivery", "推进交付", "能说明个人角色、关键行动、跨团队协作、风险处理和落地结果。", 18, ("个人角色明确", "关键动作具体", "能处理协作分歧", "交付稳定"), ("角色不清", "过程一笔带过", "只说沟通", "风险意识弱")),
            CompetencyDimension("data_impact", "数据结果", "能用数据、用户反馈、前后对比或业务影响证明项目价值。", 14, ("有量化结果", "能解释归因", "知道业务影响", "有复盘改进"), ("只说上线", "没有指标", "结果和行动脱节", "缺少反思")),
            CompetencyDimension("communication_reflection", "表达复盘", "表达结构清楚，能回应追问，并对失败、取舍和改进有反思。", 8, ("表达结构清楚", "追问下稳定", "反思具体", "改进可执行"), ("表达散", "追问失焦", "反思空泛", "改进不可执行")),
        ),
        question_seeds=("讲一个你定义需求的项目", "讲一次跨团队推进", "讲一个结果最明确的项目", "你为什么适合这个岗位"),
    ),
    RoleTemplate(
        id="operations",
        label="运营",
        generic_jd="负责用户增长、活动策划、内容/社群运营、数据复盘和跨部门资源协调。",
        competencies=(
            CompetencyDimension("role_core", "运营专业力", "掌握用户增长、活动机制、内容/社群运营和转化链路。", 24, ("目标用户明确", "运营策略具体", "转化链路清楚", "机制有效"), ("只说做活动", "人群模糊", "策略泛", "链路不清")),
            CompetencyDimension("business_understanding", "业务理解", "理解业务目标、用户价值、平台生态和商业化边界。", 18, ("理解业务目标", "知道用户价值", "连接平台生态", "动机可信"), ("只讲执行", "不了解业务", "平台理解弱", "动机模板化")),
            CompetencyDimension("problem_analysis", "问题分析", "能拆解运营问题，识别核心指标、用户动机和约束条件。", 16, ("指标定义清楚", "用户动机明确", "问题拆解合理", "约束清楚"), ("只看总量", "动机模糊", "问题泛", "约束不清")),
            CompetencyDimension("execution_delivery", "推进交付", "能组织资源、设计节奏、处理风险并稳定落地。", 18, ("执行节奏具体", "资源诉求明确", "能控风险", "交付稳定"), ("执行链路粗", "资源不清", "风险预案不足", "节奏混乱")),
            CompetencyDimension("data_impact", "数据结果", "能用数据复盘运营效果，解释归因并提出优化动作。", 16, ("会拆漏斗", "有转化指标", "知道归因边界", "优化可执行"), ("没有指标", "不会拆指标", "过度归因", "优化泛")),
            CompetencyDimension("communication_reflection", "表达复盘", "能清楚表达策略逻辑、协作过程、失败复盘和下一步计划。", 8, ("表达结构清楚", "协作对象清楚", "复盘具体", "下一步明确"), ("表达散", "只说沟通", "复盘空泛", "下一步不清")),
        ),
        question_seeds=("讲一次你做过的运营活动", "讲一个增长或转化项目", "讲一次数据复盘", "讲一次跨团队资源协调"),
    ),
    RoleTemplate(
        id="data_analyst",
        label="数据分析师",
        generic_jd="负责业务问题拆解、数据提取与分析、指标体系建设、洞察表达和决策支持。",
        competencies=(
            CompetencyDimension("role_core", "分析专业力", "掌握指标体系、分析方法、SQL/Python/BI 和数据质量校验。", 24, ("指标定义准确", "方法匹配问题", "工具使用具体", "质量校验"), ("指标含糊", "套方法", "只列工具", "不校验数据")),
            CompetencyDimension("business_understanding", "业务理解", "理解业务目标、决策场景、使用方需求和分析价值。", 18, ("业务问题清楚", "决策场景明确", "影响对象清楚", "建议可落地"), ("上来就取数", "场景不清", "业务听不懂", "建议泛")),
            CompetencyDimension("problem_analysis", "问题分析", "能把业务问题拆成假设、指标、口径、样本和分析边界。", 20, ("假设可验证", "口径严谨", "边界明确", "有对比组"), ("没有假设", "口径不清", "边界不清", "没有对比")),
            CompetencyDimension("execution_delivery", "推进交付", "能推动数据获取、跨团队沟通、看板/报告交付和决策闭环。", 12, ("数据获取顺畅", "协作清楚", "交付稳定", "决策闭环"), ("等数据", "协作不清", "交付粗糙", "没有闭环")),
            CompetencyDimension("data_impact", "数据结果", "能产出明确洞察，用结果证明分析推动了业务改进。", 18, ("结论明确", "有业务影响", "知道归因边界", "结果可衡量"), ("只堆图表", "影响不清", "因果乱判", "没有结果")),
            CompetencyDimension("communication_reflection", "表达复盘", "能把复杂分析讲清楚，并反思方法局限与下一步验证。", 8, ("表达有重点", "解释口径", "知道局限", "下一步清楚"), ("重点散", "口径解释弱", "不知道局限", "下一步不清")),
        ),
        question_seeds=("讲一个你拆解业务问题的分析项目", "讲一次你用数据影响决策", "讲一个指标体系或看板项目", "讲一次分析结论被质疑的经历"),
    ),
    RoleTemplate(
        id="frontend_engineer",
        label="前端工程师",
        generic_jd="负责前端业务开发、交互体验实现、工程质量、性能优化和跨端/跨团队协作。",
        competencies=(
            CompetencyDimension("role_core", "工程专业力", "掌握组件设计、状态管理、可维护性、测试、错误处理和工程规范。", 24, ("结构清楚", "状态边界明确", "有测试意识", "错误处理完整"), ("只会堆页面", "状态混乱", "不测", "异常无兜底")),
            CompetencyDimension("business_understanding", "业务理解", "理解用户场景、业务目标、产品体验和技术取舍。", 16, ("理解用户路径", "知道业务目标", "能提出体验改进", "能权衡成本"), ("只接需求", "不问场景", "忽略体验", "不会取舍")),
            CompetencyDimension("problem_analysis", "问题分析", "能定位复杂交互、状态、性能或联调问题，并解释边界。", 18, ("能定位瓶颈", "边界清楚", "问题拆解合理", "方案有依据"), ("凭感觉改", "边界不清", "问题泛", "方案无依据")),
            CompetencyDimension("execution_delivery", "协作交付", "能和产品、设计、后端协作处理接口、联调、风险和上线。", 18, ("接口边界清楚", "联调稳定", "风险前置", "交付稳定"), ("等别人给", "接口问题甩锅", "风险后置", "沟通空泛")),
            CompetencyDimension("data_impact", "性能结果", "能用指标说明性能、体验、质量或业务结果的优化效果。", 16, ("有性能指标", "结果可量化", "用户体验改善", "质量提升"), ("不知道指标", "没有结果", "体验无证据", "质量不可见")),
            CompetencyDimension("communication_reflection", "表达复盘", "能清楚讲工程方案、复盘问题、总结经验并提出改进。", 8, ("表达有重点", "复盘具体", "经验可迁移", "改进明确"), ("重点散", "复盘空泛", "经验不可迁移", "改进不清")),
        ),
        question_seeds=("讲一个复杂前端项目", "讲一次性能优化", "讲一次你改善用户体验的经历", "讲一次跨团队联调问题"),
    ),
)

TRAINING_OPTIONS = {
    "jobs": [{"id": role.id, "label": role.label} for role in ROLE_TEMPLATES],
    "modes": [
        {"id": "standard", "label": "标准训练"},
        {"id": "guided", "label": "引导训练"},
        {"id": "challenge", "label": "压力追问"},
    ],
    "competencies": [
        {"id": "requirement_analysis", "label": "需求分析"},
        {"id": "project_delivery", "label": "项目推进"},
        {"id": "impact_expression", "label": "结果表达"},
    ],
    "strategies": [
        {"id": "clarification_probe", "label": "澄清追问"},
        {"id": "evidence_probe", "label": "证据追问"},
        {"id": "result_probe", "label": "结果追问"},
        {"id": "reflection_probe", "label": "复盘追问"},
    ],
    "questionStyles": [
        {"id": "open", "label": "开放提问", "defaultWeight": 30},
        {"id": "evidence", "label": "证据追问", "defaultWeight": 30},
        {"id": "pressure", "label": "压力追问", "defaultWeight": 15},
        {"id": "relaxed", "label": "轻松提问", "defaultWeight": 15},
        {"id": "reflection", "label": "复盘提问", "defaultWeight": 10},
    ],
}

VOICE_PROFILES: tuple[VoiceProfile, ...] = (
    VoiceProfile(
        id="gentle_female_young",
        label="温和年轻女面试官",
        gender="female",
        age_style="young",
        voice_name="zh-CN-XiaoxiaoNeural",
        rate="+12%",
        pitch="+4Hz",
        volume="+0%",
        tone="encouraging",
        interviewer_style_prompt="语气温和、清晰、有鼓励感，问题简洁但不压迫。",
    ),
    VoiceProfile(
        id="formal_male_adult",
        label="正式成熟男面试官",
        gender="male",
        age_style="adult",
        voice_name="zh-CN-YunxiNeural",
        rate="+6%",
        pitch="-2Hz",
        volume="+0%",
        tone="formal",
        interviewer_style_prompt="语气正式克制，像真实一面面试官，追问直接但保持礼貌。",
    ),
    VoiceProfile(
        id="senior_male_calm",
        label="资深沉稳男面试官",
        gender="male",
        age_style="senior",
        voice_name="zh-CN-YunjianNeural",
        rate="+0%",
        pitch="-6Hz",
        volume="+0%",
        tone="calm",
        interviewer_style_prompt="语气沉稳，关注结构、边界和业务判断，追问更像资深面试官。",
    ),
    VoiceProfile(
        id="sharp_female_pressure",
        label="清晰压力女面试官",
        gender="female",
        age_style="adult",
        voice_name="zh-CN-XiaoyiNeural",
        rate="+10%",
        pitch="+2Hz",
        volume="+0%",
        tone="pressure",
        interviewer_style_prompt="语气更短、更直接，重点挑战证据和逻辑，但不得攻击候选人。",
    ),
    VoiceProfile(
        id="friendly_relaxed",
        label="亲和轻松面试官",
        gender="female",
        age_style="adult",
        voice_name="zh-CN-XiaoxiaoNeural",
        rate="+8%",
        pitch="+2Hz",
        volume="+0%",
        tone="relaxed",
        interviewer_style_prompt="语气亲和自然，先帮候选人进入状态，再逐步追问。",
    ),
)


def role_by_id(role_id: str) -> RoleTemplate:
    return next((role for role in ROLE_TEMPLATES if role.id == role_id), ROLE_TEMPLATES[0])


def voice_profile_by_id(profile_id: str) -> VoiceProfile:
    return next((profile for profile in VOICE_PROFILES if profile.id == profile_id), VOICE_PROFILES[0])


# 能力轨道 ID 到预设能力维度名称关键词的映射，用于匹配
_TRACK_COMPETENCY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "requirement_analysis": ("需求", "分析", "问题"),
    "project_delivery": ("推进", "交付", "执行", "协作"),
    "impact_expression": ("数据", "结果", "性能", "表达", "复盘"),
}


def _match_track_to_competency(track_id: str, comp_name: str) -> bool:
    keywords = _TRACK_COMPETENCY_KEYWORDS.get(track_id, ())
    return any(kw in comp_name for kw in keywords)


def role_template_to_dynamic_model(role: RoleTemplate) -> DynamicJobModel:
    """将预设 RoleTemplate 转换为 DynamicJobModel，用于统一处理路径。"""
    # 将 percentage 权重 (sum~100) 转为 1-10 importance 分数
    max_w = max(comp.default_weight for comp in role.competencies) if role.competencies else 1
    dynamic_comps = tuple(
        DynamicCompetency(
            id=comp.id,
            name=comp.name,
            description=comp.description,
            weight=max(1, min(10, round(comp.default_weight / max_w * 10))),
            observable_signals=comp.observable_signals,
            weak_signals=comp.weak_signals,
        )
        for comp in role.competencies
    )

    # 从 CAPABILITY_TRACKS 匹配证据要求
    evidence_reqs: list[tuple[str, tuple[DynamicEvidenceRequirement, ...]]] = []
    for track in CAPABILITY_TRACKS:
        for comp in role.competencies:
            if _match_track_to_competency(track.id, comp.name):
                evidence_reqs.append((comp.id, tuple(
                    DynamicEvidenceRequirement(
                        id=req.id,
                        name=req.name,
                        description=req.description,
                        keywords=req.keywords,
                    )
                    for req in track.requirements
                )))
                break

    # 对没有匹配到 CAPABILITY_TRACKS 的能力，从 observable_signals 自动生成
    matched_ids = {cid for cid, _ in evidence_reqs}
    for comp in role.competencies:
        if comp.id in matched_ids:
            continue
        auto_reqs = tuple(
            DynamicEvidenceRequirement(
                id=f"preset_{comp.id}_{i}",
                name=sig,
                description=f"回答中需要体现：{sig}",
                keywords=tuple(sig[:4]) if len(sig) >= 4 else (sig,),
            )
            for i, sig in enumerate(comp.observable_signals[:4])
        )
        if auto_reqs:
            evidence_reqs.append((comp.id, auto_reqs))

    # 使用通用 RUBRIC_DIMENSIONS
    dynamic_rubric = tuple(
        DynamicRubricDimension(
            id=rd.id,
            name=rd.name,
            description=rd.description,
            weak_anchor=rd.weak_anchor,
            normal_anchor=rd.normal_anchor,
            strong_anchor=rd.strong_anchor,
        )
        for rd in RUBRIC_DIMENSIONS
    )

    comp_weights = {comp.id: int(comp.default_weight) for comp in role.competencies}

    return DynamicJobModel(
        job_title=role.label,
        job_summary=role.generic_jd,
        core_requirements=tuple(comp.name for comp in role.competencies)[:5],
        interview_focus=tuple(role.question_seeds),
        competencies=dynamic_comps,
        question_seeds=role.question_seeds,
        competency_weights=comp_weights,
        question_style_weights={"open": 30, "evidence": 30, "pressure": 15, "relaxed": 15, "reflection": 10},
        focus_competency_id=role.competencies[0].id if role.competencies else "role_core",
        focus_question_style_id="open",
        evidence_requirements=tuple(evidence_reqs),
        rubric_dimensions=dynamic_rubric,
        recommended_voice={"voiceProfileId": "gentle_female_young", "interviewerTone": "encouraging", "voiceRate": "+8%", "voicePitch": "+2Hz", "voiceVolume": "+0%"},
        analysis_notes=(f"使用{role.label}预设模板配置。",),
        analysis_source="template_fallback",
        opening_question=PRODUCT_MANAGER_OPENING,
    )


def dynamic_model_for_role(role_id: str) -> DynamicJobModel:
    """根据预设岗位 ID 获取对应的 DynamicJobModel。"""
    role = role_by_id(role_id)
    return role_template_to_dynamic_model(role)


def role_capability_options(role_id: str) -> list[dict[str, object]]:
    role = role_by_id(role_id)
    return [
        {
            "id": item.id,
            "label": item.name,
            "description": item.description,
            "defaultWeight": item.default_weight,
            "observableSignals": list(item.observable_signals),
            "weakSignals": list(item.weak_signals),
        }
        for item in role.competencies
    ]


def interview_options_payload() -> dict[str, object]:
    return {
        **TRAINING_OPTIONS,
        "roles": [
            {
                "id": role.id,
                "label": role.label,
                "genericJd": role.generic_jd,
                "competencies": role_capability_options(role.id),
                "questionSeeds": list(role.question_seeds),
            }
            for role in ROLE_TEMPLATES
        ],
        "voiceProfiles": [
            {
                "id": profile.id,
                "label": profile.label,
                "gender": profile.gender,
                "ageStyle": profile.age_style,
                "voiceName": profile.voice_name,
                "rate": profile.rate,
                "pitch": profile.pitch,
                "volume": profile.volume,
                "tone": profile.tone,
            }
            for profile in VOICE_PROFILES
        ],
    }

MODE_BEHAVIOR = {
    "standard": "保持专业、自然、中等压力，像真实结构化面试。",
    "guided": "追问更温和，必要时给方向提示，但不要直接替候选人作答。",
    "challenge": "追问更尖锐，重点检验证据、稳定性和边界，但不要攻击候选人。",
}

STRATEGY_FOCUS = {
    "clarification_probe": "优先澄清背景、角色、问题定义和上下文。",
    "evidence_probe": "优先追问细节、数据、用户反馈、前后对比和个人贡献。",
    "result_probe": "优先追问结果、指标、业务影响和结果归因。",
    "reflection_probe": "优先追问复盘、取舍、失败、如果重做会怎么改。",
}

CAPABILITY_TRACKS: tuple[CapabilityTrack, ...] = (
    CapabilityTrack(
        id="requirement_analysis",
        name="需求分析",
        description="识别真实用户问题，解释判断依据、优先级和验证方式。",
        requirements=(
            EvidenceRequirement("demand_source", "需求来源", "需求从哪里来，为什么值得关注。", ("需求", "反馈", "用户", "调研", "访谈")),
            EvidenceRequirement("user_problem", "用户问题", "用户是谁，真实痛点是什么。", ("痛点", "问题", "场景", "用户", "困扰")),
            EvidenceRequirement("decision_basis", "判断依据", "为什么这样判断和排序。", ("依据", "优先级", "判断", "取舍", "价值")),
            EvidenceRequirement("validation", "验证方式", "如何验证需求或方案有效。", ("验证", "测试", "数据", "实验", "上线")),
        ),
    ),
    CapabilityTrack(
        id="project_delivery",
        name="项目推进",
        description="讲清个人角色、关键行动、协作对象、约束处理和交付结果。",
        requirements=(
            EvidenceRequirement("personal_role", "个人角色", "自己负责什么，不把团队成果笼统归到自己身上。", ("我负责", "我主要", "我的角色", "我推动")),
            EvidenceRequirement("key_actions", "关键行动", "做了哪些关键动作或决策。", ("推进", "协调", "设计", "梳理", "落地")),
            EvidenceRequirement("stakeholders", "协作对象", "和谁协作，有什么分歧或约束。", ("研发", "设计", "运营", "业务", "沟通", "协作")),
            EvidenceRequirement("constraint_handling", "约束处理", "如何处理冲突、资源、时间或风险。", ("风险", "冲突", "延期", "资源", "约束")),
        ),
    ),
    CapabilityTrack(
        id="impact_expression",
        name="结果表达",
        description="用具体结果、数据、用户反馈或前后对比证明项目影响。",
        requirements=(
            EvidenceRequirement("outcome", "项目结果", "项目最后产生了什么变化。", ("结果", "上线", "完成", "落地", "变化")),
            EvidenceRequirement("metrics", "量化指标", "有没有数字、比例、时长、转化等量化证据。", ("提升", "降低", "%", "数据", "指标", "转化")),
            EvidenceRequirement("attribution", "贡献归因", "能否说明结果与自己行动之间的关系。", ("因为我", "通过", "推动", "贡献", "负责")),
            EvidenceRequirement("reflection", "复盘反思", "知道哪里可改进，下一次会怎么做。", ("复盘", "反思", "如果重做", "下次", "改进")),
        ),
    ),
)

RUBRIC_DIMENSIONS: tuple[RubricDimension, ...] = (
    RubricDimension(
        id="answer_structure",
        name="回答结构",
        description="回答是否有清晰的背景、目标、行动、结果和反思。",
        weak_anchor="信息散乱，只是在罗列经历，听不出主线。",
        normal_anchor="有基本结构，但重点、因果和转折不够突出。",
        strong_anchor="能在有限时间内清楚说明背景、目标、行动、结果和反思。",
    ),
    RubricDimension(
        id="experience_evidence",
        name="经历证据",
        description="是否用细节、数据、场景或反馈证明自己的贡献。",
        weak_anchor="泛泛描述，缺少可验证证据和个人贡献。",
        normal_anchor="有部分细节或结果，但证据链不完整。",
        strong_anchor="能给出具体行动、数据变化、用户反馈或前后对比。",
    ),
    RubricDimension(
        id="job_understanding",
        name="岗位理解",
        description="是否体现岗位需要的问题判断、优先级、协作和结果意识。",
        weak_anchor="更像执行任务，没有体现岗位判断和业务语境。",
        normal_anchor="能体现部分岗位意识，但和目标岗位能力连接不够稳定。",
        strong_anchor="能把项目经历和目标岗位核心能力自然连接起来。",
    ),
    RubricDimension(
        id="project_delivery",
        name="项目推进",
        description="是否能说明自己的推进动作、协作过程和约束处理。",
        weak_anchor="个人角色不清，推进过程被一笔带过。",
        normal_anchor="能说出角色和行动，但冲突、风险或协作细节不足。",
        strong_anchor="能讲清个人角色、关键行动、协作约束、风险处理和交付结果。",
    ),
    RubricDimension(
        id="expression_clarity",
        name="表达清晰度",
        description="表达是否自然、简洁、稳定，是否适合真实面试沟通。",
        weak_anchor="表达绕、虚或不稳定，追问后容易失焦。",
        normal_anchor="表达基本清楚，但重点和节奏还可以更稳定。",
        strong_anchor="表达具体、自然、有重点，追问下仍能稳定补充。",
    ),
)
