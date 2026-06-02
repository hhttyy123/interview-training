from interview.models import RubricDimension


PRODUCT_MANAGER_OPENING = "你好，我们开始一轮产品经理项目经历深挖。请先用一分钟介绍一个最能代表你产品能力的项目。"

PRODUCT_MANAGER_COMPETENCIES = (
    "需求分析：是否能区分用户表层需求和真实问题，并说明判断依据。",
    "项目推进：是否能讲清楚自己的角色、关键动作、协作对象和约束处理。",
    "结果表达：是否能说明项目上线后带来的变化，并尽量给出数据或具体证据。",
    "产品思考：是否能解释取舍、优先级、验证方式和复盘反思。",
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
    "standard": "保持专业、自然、适中压力，像真实结构化面试。",
    "guided": "追问更温和，必要时给一点方向提示，但不要直接替候选人作答。",
    "challenge": "追问更尖锐，重点检验稳定性、证据和边界，但不要攻击候选人。",
}

COMPETENCY_FOCUS = {
    "requirement_analysis": "重点观察需求分析：真实用户问题、判断依据、优先级和验证方式。",
    "project_delivery": "重点观察项目推进：个人角色、协作对象、约束处理、风险和交付结果。",
    "impact_expression": "重点观察结果表达：结构、数据证据、个人贡献、结果归因和业务影响。",
}

STRATEGY_FOCUS = {
    "clarification_probe": "优先做澄清追问，先把背景、角色和问题定义问清楚。",
    "evidence_probe": "优先做证据追问，要求候选人补充细节、数据、反馈或前后对比。",
    "result_probe": "优先做结果追问，关注项目上线后变化、指标、用户反馈和影响。",
    "reflection_probe": "优先做复盘追问，关注候选人的反思、取舍和如果重做会怎么改。",
}

RUBRIC_DIMENSIONS: tuple[RubricDimension, ...] = (
    RubricDimension(
        id="structure",
        name="回答结构",
        description="回答是否有清晰的背景、目标、行动、结果和反思顺序。",
        weak_anchor="信息散乱，只是在罗列经历，听不出主线。",
        strong_anchor="能用清晰结构讲出项目背景、个人动作、结果和复盘。",
    ),
    RubricDimension(
        id="evidence",
        name="经历证据",
        description="是否用真实细节、数据、场景或反馈证明自己的贡献。",
        weak_anchor="只有泛泛描述，缺少可验证证据和个人贡献。",
        strong_anchor="能给出具体动作、数据变化、用户反馈或前后对比。",
    ),
    RubricDimension(
        id="job_understanding",
        name="岗位理解",
        description="是否体现产品经理岗位需要的需求判断、优先级、协作和结果意识。",
        weak_anchor="更像执行任务，没有体现产品判断和岗位语境。",
        strong_anchor="能把项目表达和产品经理核心能力自然连接起来。",
    ),
    RubricDimension(
        id="expression",
        name="表达清晰度",
        description="表达是否自然、简洁、稳定，是否适合真实面试沟通。",
        weak_anchor="表达绕、虚或不稳定，追问后容易失焦。",
        strong_anchor="表达具体、自然、有重点，追问下仍能稳定补充。",
    ),
)
