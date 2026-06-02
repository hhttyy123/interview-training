from interview.models import CapabilityTrack, EvidenceRequirement, RubricDimension


PRODUCT_MANAGER_OPENING = (
    "你好，我们开始一轮项目经历深挖。"
    "请先用一分钟介绍一个最能代表你岗位能力的项目。"
)

TRAINING_OPTIONS = {
    "jobs": [{"id": "product_manager", "label": "产品经理"}],
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
