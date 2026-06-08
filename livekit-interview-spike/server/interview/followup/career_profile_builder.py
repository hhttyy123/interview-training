from __future__ import annotations

import re
from dataclasses import dataclass

from interview.followup.models import (
    CareerProfile,
    CompetencyArchetype,
    EvidenceCategory,
    EvidenceQualityBar,
    EvidenceSlot,
    RoleFamily,
)


@dataclass(frozen=True)
class RoleFamilySignal:
    role_family: RoleFamily
    keywords: tuple[str, ...]
    core_work_objects: tuple[str, ...]
    typical_tasks: tuple[str, ...]
    common_deliverables: tuple[str, ...]
    success_metrics: tuple[str, ...]
    collaboration_objects: tuple[str, ...]
    risk_types: tuple[str, ...]
    default_archetypes: tuple[CompetencyArchetype, ...]


@dataclass(frozen=True)
class CompetencySignal:
    archetype: CompetencyArchetype
    keywords: tuple[str, ...]


def build_career_profile(
    *,
    role_title: str,
    jd_text: str = "",
    user_context: str = "",
) -> CareerProfile:
    source_text = _normalize_text(" ".join([role_title, jd_text, user_context]))
    family = _infer_role_family(source_text)
    family_signal = _family_signal(family)
    archetypes = _infer_competency_archetypes(source_text, family_signal.default_archetypes)
    confidence = _confidence(source_text, family, archetypes)

    return CareerProfile(
        role_title=role_title.strip() or "未命名岗位",
        role_family=family,
        seniority=_infer_seniority(source_text),
        work_mode=_infer_work_mode(source_text),
        core_work_objects=family_signal.core_work_objects,
        typical_tasks=family_signal.typical_tasks,
        common_deliverables=family_signal.common_deliverables,
        success_metrics=family_signal.success_metrics,
        collaboration_objects=family_signal.collaboration_objects,
        risk_types=family_signal.risk_types,
        competency_archetypes=archetypes,
        source="dynamic_jd" if jd_text.strip() else "user_input",
        confidence=confidence,
    )


def build_evidence_slots_for_career(career_profile: CareerProfile) -> list[EvidenceSlot]:
    archetypes = career_profile.competency_archetypes or ("problem_framing", "execution_delivery", "learning_reflection")
    slots: list[EvidenceSlot] = []
    for index, archetype in enumerate(archetypes):
        for category in _evidence_categories_for_archetype(archetype):
            slots.append(
                EvidenceSlot(
                    id=f"{career_profile.role_family}.{archetype}.{category}",
                    competency_id=archetype,
                    label=_slot_label(archetype, category),
                    category=category,
                    required=_is_required_category(category),
                    priority=90 - index * 4 if _is_required_category(category) else 55 - index * 3,
                    quality_bar=_quality_bar(category),
                )
            )
    return _dedupe_slots(slots)


def _infer_role_family(text: str) -> RoleFamily:
    scored = sorted(
        ((_score_keywords(text, signal.keywords), signal.role_family) for signal in ROLE_FAMILY_SIGNALS),
        reverse=True,
    )
    best_score, best_family = scored[0]
    return best_family if best_score > 0 else "general"


def _infer_competency_archetypes(
    text: str,
    defaults: tuple[CompetencyArchetype, ...],
) -> tuple[CompetencyArchetype, ...]:
    scores = [
        (_score_keywords(text, signal.keywords), signal.archetype)
        for signal in COMPETENCY_SIGNALS
    ]
    selected = [archetype for score, archetype in sorted(scores, reverse=True) if score > 0]
    merged = [*selected, *defaults, "communication_expression", "learning_reflection"]
    return tuple(dict.fromkeys(merged))[:6]


def _infer_seniority(text: str) -> str:
    if _contains_any(text, ("专家", "负责人", "总监", "principal", "lead", "head", "director")):
        return "senior_lead"
    if _contains_any(text, ("高级", "资深", "senior", "sr.")):
        return "senior"
    if _contains_any(text, ("实习", "校招", "应届", "intern", "graduate")):
        return "entry"
    if _contains_any(text, ("初级", "助理", "junior", "assistant")):
        return "junior"
    return "unknown"


def _infer_work_mode(text: str) -> str:
    if _contains_any(text, ("远程", "remote")):
        return "remote"
    if _contains_any(text, ("混合", "hybrid")):
        return "hybrid"
    if _contains_any(text, ("现场", "驻场", "onsite")):
        return "onsite"
    return "unknown"


def _confidence(text: str, family: RoleFamily, archetypes: tuple[CompetencyArchetype, ...]) -> float:
    score = 0.35
    if len(text) >= 40:
        score += 0.2
    if family != "general":
        score += 0.25
    if len(archetypes) >= 4:
        score += 0.1
    return min(score, 0.9)


def _evidence_categories_for_archetype(archetype: CompetencyArchetype) -> tuple[EvidenceCategory, ...]:
    return ARCHETYPE_EVIDENCE_CATEGORIES.get(archetype, ("context", "action", "result", "learning"))


def _slot_label(archetype: CompetencyArchetype, category: EvidenceCategory) -> str:
    archetype_label = ARCHETYPE_LABELS.get(archetype, archetype)
    category_label = CATEGORY_LABELS.get(category, category)
    return f"{archetype_label}：{category_label}"


def _quality_bar(category: EvidenceCategory) -> EvidenceQualityBar:
    return QUALITY_BARS.get(
        category,
        EvidenceQualityBar(
            unacceptable="只有主观评价，没有可验证信息。",
            weak="提到相关经历，但缺少场景、动作或结果。",
            acceptable="能说明具体场景、个人动作和基本结果。",
            strong="能说明约束、权衡、可验证结果、反馈来源和复盘。",
        ),
    )


def _is_required_category(category: EvidenceCategory) -> bool:
    return category in {"context", "task", "action", "decision", "result", "metric", "technical_depth", "business_judgment"}


def _dedupe_slots(slots: list[EvidenceSlot]) -> list[EvidenceSlot]:
    deduped: dict[tuple[str, EvidenceCategory], EvidenceSlot] = {}
    for slot in slots:
        key = (slot.competency_id, slot.category)
        if key not in deduped or slot.priority > deduped[key].priority:
            deduped[key] = slot
    return sorted(deduped.values(), key=lambda item: item.priority, reverse=True)


def _family_signal(role_family: RoleFamily) -> RoleFamilySignal:
    for signal in ROLE_FAMILY_SIGNALS:
        if signal.role_family == role_family:
            return signal
    return GENERAL_SIGNAL


def _score_keywords(text: str, keywords: tuple[str, ...]) -> int:
    return sum(2 if keyword in text else 0 for keyword in keywords)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


GENERAL_SIGNAL = RoleFamilySignal(
    role_family="general",
    keywords=(),
    core_work_objects=("业务目标", "工作任务", "协作对象", "交付结果"),
    typical_tasks=("理解目标", "拆解任务", "推进执行", "复盘优化"),
    common_deliverables=("方案", "计划", "过程记录", "结果复盘"),
    success_metrics=("目标达成度", "交付质量", "协作效率", "学习迁移"),
    collaboration_objects=("直属负责人", "同事", "跨职能伙伴", "用户或客户"),
    risk_types=("目标不清", "资源不足", "沟通偏差", "结果不可验证"),
    default_archetypes=("problem_framing", "execution_delivery", "collaboration_influence"),
)


ROLE_FAMILY_SIGNALS: tuple[RoleFamilySignal, ...] = (
    RoleFamilySignal(
        "engineering",
        ("工程", "研发", "开发", "后端", "前端", "客户端", "算法", "架构", "测试", "dev", "engineer", "developer"),
        ("系统", "代码", "服务", "架构", "性能", "稳定性"),
        ("需求澄清", "技术设计", "编码实现", "测试验证", "故障处理"),
        ("设计文档", "代码提交", "接口", "测试报告", "上线复盘"),
        ("稳定性", "性能", "缺陷率", "交付周期", "可维护性"),
        ("产品", "测试", "运维", "设计", "业务方"),
        ("技术债", "性能瓶颈", "线上故障", "边界条件遗漏"),
        ("technical_depth", "problem_framing", "execution_delivery", "compliance_risk_awareness"),
    ),
    RoleFamilySignal(
        "product_business",
        ("产品", "需求", "用户", "商业化", "增长", "策略", "product", "pm"),
        ("用户问题", "业务目标", "产品能力", "数据指标"),
        ("需求洞察", "方案设计", "优先级判断", "推动上线", "效果复盘"),
        ("PRD", "原型", "路线图", "指标分析", "复盘报告"),
        ("转化率", "留存", "活跃", "收入", "满意度"),
        ("研发", "设计", "运营", "数据", "业务方"),
        ("需求误判", "优先级冲突", "资源约束", "指标归因偏差"),
        ("customer_user_understanding", "commercial_judgment", "problem_framing", "collaboration_influence"),
    ),
    RoleFamilySignal(
        "operations_growth",
        ("运营", "增长", "活动", "社群", "内容", "投放", "growth", "operation"),
        ("用户群体", "渠道", "活动机制", "内容资产", "增长指标"),
        ("用户分层", "活动策划", "渠道优化", "数据复盘", "流程提效"),
        ("活动方案", "运营节奏", "数据看板", "复盘报告"),
        ("拉新", "转化", "留存", "活跃", "ROI"),
        ("产品", "市场", "销售", "数据", "客服"),
        ("指标虚高", "渠道质量差", "执行断点", "预算浪费"),
        ("analytical_reasoning", "execution_delivery", "customer_user_understanding", "commercial_judgment"),
    ),
    RoleFamilySignal(
        "data_analytics",
        ("数据", "分析", "bi", "数仓", "统计", "实验", "analytics", "analyst"),
        ("数据源", "指标体系", "分析模型", "实验结果"),
        ("定义口径", "清洗数据", "分析归因", "输出洞察", "支持决策"),
        ("分析报告", "仪表盘", "指标口径", "实验结论"),
        ("数据准确性", "洞察采纳率", "决策影响", "分析时效"),
        ("业务方", "产品", "研发", "算法", "管理层"),
        ("口径不一致", "样本偏差", "相关不等于因果", "数据质量问题"),
        ("analytical_reasoning", "business_judgment", "problem_framing", "communication_expression"),
    ),
    RoleFamilySignal(
        "design_creative",
        ("设计", "视觉", "交互", "体验", "品牌", "创意", "ui", "ux", "designer"),
        ("用户体验", "视觉系统", "交互路径", "品牌表达"),
        ("理解需求", "提出方案", "验证体验", "交付设计", "推动落地"),
        ("设计稿", "原型", "设计规范", "用户测试结论"),
        ("可用性", "转化", "满意度", "一致性", "交付效率"),
        ("产品", "研发", "运营", "品牌", "用户研究"),
        ("审美主观化", "落地成本过高", "用户验证不足", "规范不一致"),
        ("creative_solution", "customer_user_understanding", "communication_expression", "collaboration_influence"),
    ),
    RoleFamilySignal(
        "sales_customer",
        ("销售", "客户", "商务", "售前", "客服", "成功", "bd", "sales", "customer"),
        ("客户需求", "商机", "合同", "服务体验", "续费关系"),
        ("挖掘需求", "推进转化", "处理异议", "维护关系", "复盘机会"),
        ("客户方案", "报价", "合同", "跟进记录", "续费计划"),
        ("成交额", "转化率", "客单价", "续费率", "满意度"),
        ("客户", "产品", "交付", "法务", "财务"),
        ("承诺过度", "需求误解", "回款风险", "客户流失"),
        ("commercial_judgment", "communication_expression", "collaboration_influence", "ownership_resilience"),
    ),
    RoleFamilySignal(
        "consulting_strategy",
        ("咨询", "战略", "研究", "行业分析", "consulting", "strategy"),
        ("行业问题", "客户目标", "商业模型", "竞争格局"),
        ("问题定义", "结构拆解", "假设验证", "方案建议", "汇报影响"),
        ("研究报告", "战略方案", "访谈纪要", "测算模型"),
        ("客户采纳", "业务影响", "洞察质量", "交付时效"),
        ("客户", "专家", "数据团队", "项目经理", "管理层"),
        ("假设偏差", "信息不足", "建议不可落地", "利益相关方分歧"),
        ("problem_framing", "analytical_reasoning", "commercial_judgment", "communication_expression"),
    ),
    RoleFamilySignal(
        "finance_risk",
        ("财务", "金融", "投资", "审计", "风控", "会计", "finance", "risk", "audit"),
        ("资金", "报表", "风险敞口", "投资标的", "合规要求"),
        ("数据核验", "风险识别", "模型测算", "流程控制", "报告输出"),
        ("财务报告", "风险评估", "审计底稿", "投资分析"),
        ("准确率", "风险暴露", "收益", "合规通过率", "处理时效"),
        ("业务方", "法务", "审计", "管理层", "监管相关方"),
        ("合规风险", "模型误差", "数据失真", "内控缺陷"),
        ("analytical_reasoning", "compliance_risk_awareness", "business_judgment", "ownership_resilience"),
    ),
    RoleFamilySignal(
        "supply_chain_manufacturing",
        ("供应链", "采购", "计划", "生产", "制造", "物流", "库存", "产能", "交付", "质量", "supply", "manufacturing"),
        ("供应商", "物料", "库存", "产能", "交付计划", "质量标准"),
        ("需求预测", "产能协调", "计划排程", "供应风险识别", "交付跟踪"),
        ("排产计划", "采购计划", "库存报表", "风险预案", "质量记录"),
        ("准交率", "库存周转", "缺货率", "良率", "成本"),
        ("供应商", "生产", "质量", "销售", "财务", "仓储物流"),
        ("供应中断", "库存积压", "质量波动", "交期延误", "成本失控"),
        ("execution_delivery", "analytical_reasoning", "compliance_risk_awareness", "collaboration_influence"),
    ),
    RoleFamilySignal(
        "hr_admin",
        ("人力", "招聘", "hr", "组织", "行政", "员工关系"),
        ("候选人", "员工", "组织流程", "制度", "雇主品牌"),
        ("需求澄清", "人才筛选", "流程推动", "关系协调", "制度落地"),
        ("招聘方案", "面试记录", "制度文档", "培训材料"),
        ("招聘周期", "到岗率", "留存", "员工满意度", "流程效率"),
        ("业务负责人", "候选人", "员工", "法务", "行政供应商"),
        ("误招", "流程不公平", "劳动风险", "沟通冲突"),
        ("communication_expression", "collaboration_influence", "compliance_risk_awareness", "execution_delivery"),
    ),
    RoleFamilySignal(
        "education_training",
        ("教育", "老师", "讲师", "培训", "课程", "teaching", "trainer"),
        ("学习者", "课程目标", "教学内容", "学习效果"),
        ("诊断问题", "设计课程", "授课辅导", "评估效果", "迭代内容"),
        ("教案", "课程大纲", "学习反馈", "评估报告"),
        ("通过率", "满意度", "学习完成率", "能力提升"),
        ("学生", "家长", "教研", "运营", "学校或企业客户"),
        ("学习目标不清", "反馈失真", "内容难度不匹配", "交付不稳定"),
        ("communication_expression", "customer_user_understanding", "learning_reflection", "execution_delivery"),
    ),
    GENERAL_SIGNAL,
)


COMPETENCY_SIGNALS: tuple[CompetencySignal, ...] = (
    CompetencySignal("problem_framing", ("拆解", "定义问题", "定位", "诊断", "目标", "问题")),
    CompetencySignal("domain_knowledge", ("行业", "领域", "专业", "知识", "政策", "市场")),
    CompetencySignal("execution_delivery", ("推进", "落地", "执行", "交付", "上线", "闭环")),
    CompetencySignal("collaboration_influence", ("协作", "沟通", "推动", "影响", "跨部门", "stakeholder")),
    CompetencySignal("analytical_reasoning", ("分析", "数据", "模型", "归因", "实验", "测算")),
    CompetencySignal("technical_depth", ("技术", "架构", "代码", "性能", "算法", "系统")),
    CompetencySignal("customer_user_understanding", ("用户", "客户", "体验", "需求", "调研")),
    CompetencySignal("commercial_judgment", ("商业", "收入", "成本", "roi", "利润", "转化")),
    CompetencySignal("creative_solution", ("创意", "设计", "方案", "创新", "视觉")),
    CompetencySignal("communication_expression", ("表达", "汇报", "演示", "文档", "说服")),
    CompetencySignal("ownership_resilience", ("负责", "抗压", "困难", "冲突", "失败")),
    CompetencySignal("learning_reflection", ("复盘", "学习", "迭代", "改进", "成长")),
    CompetencySignal("compliance_risk_awareness", ("风险", "合规", "审计", "安全", "内控")),
    CompetencySignal("leadership_planning", ("管理", "规划", "带队", "负责人", "计划")),
)


ARCHETYPE_EVIDENCE_CATEGORIES: dict[CompetencyArchetype, tuple[EvidenceCategory, ...]] = {
    "problem_framing": ("context", "task", "decision", "result"),
    "domain_knowledge": ("context", "decision", "business_judgment", "learning"),
    "execution_delivery": ("task", "action", "result", "metric"),
    "collaboration_influence": ("collaboration", "action", "result", "learning"),
    "analytical_reasoning": ("context", "decision", "metric", "business_judgment"),
    "technical_depth": ("technical_depth", "decision", "risk", "result"),
    "customer_user_understanding": ("context", "decision", "result", "metric"),
    "commercial_judgment": ("business_judgment", "decision", "metric", "risk"),
    "creative_solution": ("context", "decision", "action", "result"),
    "communication_expression": ("collaboration", "action", "result", "learning"),
    "ownership_resilience": ("context", "action", "risk", "learning"),
    "learning_reflection": ("learning", "decision", "action", "result"),
    "compliance_risk_awareness": ("risk", "decision", "result", "learning"),
    "leadership_planning": ("task", "collaboration", "decision", "result"),
}


ARCHETYPE_LABELS: dict[CompetencyArchetype, str] = {
    "problem_framing": "问题定义",
    "domain_knowledge": "领域理解",
    "execution_delivery": "执行交付",
    "collaboration_influence": "协作影响",
    "analytical_reasoning": "分析推理",
    "technical_depth": "技术深度",
    "customer_user_understanding": "用户/客户理解",
    "commercial_judgment": "商业判断",
    "creative_solution": "创造性方案",
    "communication_expression": "沟通表达",
    "ownership_resilience": "责任心与韧性",
    "learning_reflection": "学习复盘",
    "compliance_risk_awareness": "合规与风险意识",
    "leadership_planning": "规划与领导",
}


CATEGORY_LABELS: dict[EvidenceCategory, str] = {
    "context": "场景背景",
    "task": "任务目标",
    "action": "个人动作",
    "decision": "判断依据",
    "tradeoff": "权衡取舍",
    "collaboration": "协作推进",
    "result": "结果影响",
    "metric": "指标证据",
    "learning": "复盘学习",
    "company_fit": "公司匹配",
    "role_fit": "岗位匹配",
    "technical_depth": "专业深度",
    "business_judgment": "业务判断",
    "risk": "风险边界",
}


QUALITY_BARS: dict[EvidenceCategory, EvidenceQualityBar] = {
    "context": EvidenceQualityBar(
        "只说做过某事，没有背景。",
        "有背景但缺少对象、约束或问题来源。",
        "能说明对象、问题、约束和目标。",
        "能说明背景变化、关键约束、利益相关方和为什么重要。",
    ),
    "action": EvidenceQualityBar(
        "只说团队做了什么，看不出个人贡献。",
        "提到个人参与，但动作泛泛。",
        "能说明自己做了哪些关键动作。",
        "能说明动作顺序、取舍、推动方式和他人反馈。",
    ),
    "decision": EvidenceQualityBar(
        "只给结论，没有依据。",
        "有依据但缺少对比选项。",
        "能说明判断依据和被放弃的选项。",
        "能说明数据、约束、备选方案、风险和决策边界。",
    ),
    "result": EvidenceQualityBar(
        "只说效果不错。",
        "有结果但缺少可验证信息。",
        "能说明结果、反馈或前后变化。",
        "能说明指标口径、变化幅度、归因边界和持续影响。",
    ),
    "metric": EvidenceQualityBar(
        "没有指标。",
        "有数字但口径不清。",
        "能说明指标口径和变化。",
        "能说明基线、口径、样本、变化幅度和归因限制。",
    ),
    "risk": EvidenceQualityBar(
        "没有提风险。",
        "只泛泛说注意风险。",
        "能说明具体风险和应对动作。",
        "能说明风险来源、监控信号、预案和实际处置结果。",
    ),
    "learning": EvidenceQualityBar(
        "没有复盘。",
        "只说学到了很多。",
        "能说明一个具体改进点。",
        "能说明认知变化、下一次做法和可迁移经验。",
    ),
}
