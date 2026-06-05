from __future__ import annotations

import json
import re
from typing import Any

from interview.configs import role_by_id
from interview.models import (
    DynamicCompetency,
    DynamicEvidenceRequirement,
    DynamicJobModel,
    DynamicRubricDimension,
)
from local_providers import ConversationMessage, DeepSeekStreamingTextProvider


KEYWORD_RULES = {
    "role_core": ("职责", "专业", "产品", "运营", "分析", "前端", "工程", "方法", "设计", "开发"),
    "business_understanding": ("业务", "商业", "用户", "客户", "行业", "公司", "场景", "增长", "价值"),
    "problem_analysis": ("问题", "拆解", "分析", "判断", "策略", "逻辑", "方案", "调研", "洞察"),
    "execution_delivery": ("推进", "协作", "落地", "交付", "项目", "跨部门", "沟通", "资源", "风险"),
    "data_impact": ("数据", "指标", "结果", "转化", "增长", "复盘", "SQL", "Python", "BI", "性能"),
    "communication_reflection": ("表达", "汇报", "复盘", "总结", "反思", "文档", "沟通", "分享"),
}

ROLE_DEMO_WEIGHTS = {
    "product_manager": {
        "role_core": 34,
        "business_understanding": 18,
        "problem_analysis": 22,
        "execution_delivery": 14,
        "data_impact": 8,
        "communication_reflection": 4,
    },
    "operations": {
        "role_core": 30,
        "business_understanding": 16,
        "problem_analysis": 12,
        "execution_delivery": 24,
        "data_impact": 14,
        "communication_reflection": 4,
    },
    "data_analyst": {
        "role_core": 24,
        "business_understanding": 12,
        "problem_analysis": 32,
        "execution_delivery": 6,
        "data_impact": 22,
        "communication_reflection": 4,
    },
    "frontend_engineer": {
        "role_core": 36,
        "business_understanding": 8,
        "problem_analysis": 18,
        "execution_delivery": 18,
        "data_impact": 14,
        "communication_reflection": 6,
    },
}


def analyze_jd(*, role_id: str, jd_text: str) -> dict[str, object]:
    role = role_by_id(role_id)
    text = jd_text.strip() or role.generic_jd
    weights = {item.id: int(item.default_weight) for item in role.competencies}
    hits: dict[str, int] = {item.id: 0 for item in role.competencies}
    if text:
        for competency in role.competencies:
            for keyword in KEYWORD_RULES.get(competency.id, ()):
                hits[competency.id] += text.count(keyword)
        for competency_id, hit_count in hits.items():
            weights[competency_id] = min(60, max(8, weights.get(competency_id, 20) + hit_count * 3))

    total = sum(weights.values()) or 1
    normalized = {key: round(value / total * 100) for key, value in weights.items()}
    drift = 100 - sum(normalized.values())
    if normalized:
        first_key = next(iter(normalized))
        normalized[first_key] += drift
    if role.id in ROLE_DEMO_WEIGHTS:
        normalized = _blend_weights(normalized, ROLE_DEMO_WEIGHTS[role.id], ratio=0.68)
    focus_competency_id = max(normalized, key=lambda key: normalized[key])

    question_style_weights = {
        "open": 25,
        "evidence": 35 if any(word in text for word in ("数据", "指标", "结果", "SQL", "性能")) else 30,
        "pressure": 20 if any(word in text for word in ("高压", "复杂", "挑战", "owner", "独立")) else 15,
        "relaxed": 10,
        "reflection": 15,
    }

    return {
        "roleId": role.id,
        "roleLabel": role.label,
        "jdSummary": _summary_for(role.label, text),
        "coreRequirements": _core_requirements_for(role.id),
        "interviewFocus": _interview_focus_for(role.id),
        "competencyWeights": normalized,
        "questionStyleWeights": question_style_weights,
        "focusCompetencyId": focus_competency_id,
        "recommendedVoice": _recommended_voice(role.id, question_style_weights),
        "analysisNotes": _analysis_notes(role.label, hits),
        "analysisSource": "internal_seed",
    }


DYNAMIC_JOB_SYSTEM_PROMPT = """\
你是面试系统配置分析器。只输出 JSON，不输出 Markdown。

根据目标岗位和可选 JD/公司信息，生成完整面试模型。输出结构：

{
  "jobSummary": "120字岗位摘要",
  "coreRequirements": ["可观察要求", ...], // 3-5条
  "interviewFocus": ["追问方向", ...], // 3-5条
  "competencies": [{
    "id": "comp_0", "name": "能力名(岗位定制,勿用笼统词)", "description": "1-2句",
    "importance": 8, // 1-10整数, 该能力在本岗位的重要性(独立评分, 可多个相同分数)
    "observableSignals": ["正面信号"], "weakSignals": ["不足信号"] // 各3-5个
  }], // 4-7个
  "questionSeeds": ["种子问题"], // 3-5个
  "evidenceRequirements": [{
    "competencyId": "comp_0",
    "requirements": [{"id":"ev_0_0","name":"证据名","description":"验证什么","keywords":["关键词"]}] // 每能力3-5个, 关键词3-8个
  }],
  "rubricDimensions": [{
    "id":"dim_0","name":"评分维度","description":"评什么",
    "weakAnchor":"2分行为描述","normalAnchor":"6分行为描述","strongAnchor":"9-10分行为描述"
  }], // 4-6个
  "openingQuestion": "60字以内自然开场",
  "questionStyleWeights": {"open":25,"evidence":35,"pressure":15,"relaxed":10,"reflection":15},
  "focusCompetencyId": "comp_0",
  "recommendedVoice": {"voiceProfileId":"gentle_female_young","interviewerTone":"encouraging","voiceRate":"+8%","voicePitch":"+2Hz","voiceVolume":"+0%"},
  "analysisNotes": ["设计理由1","设计理由2"]
}

约束:
- importance 为 1-10 整数，独立评分（不要求总和=100），多个能力可有相同分数
- 核心能力 7-10 分，辅助能力 4-6 分，边缘能力 1-3 分
- 能力名必须岗位定制(销售→客户开发, 技术→系统设计), 禁用"岗位专业力"等笼统词
- rubric anchor 必须具体行为, 不可说"表现好/差"
- challenge模式pressure>=30, guided模式relaxed/open明显更高
- voiceProfileId: gentle_female_young/formal_male_adult/senior_male_calm/sharp_female_pressure/friendly_relaxed
- interviewerTone: encouraging/formal/pressure/relaxed/calm
"""


async def analyze_dynamic_job(
    *,
    job_title: str,
    mode_id: str = "standard",
    jd_text: str = "",
    company_card: dict[str, Any] | None = None,
) -> DynamicJobModel:
    """对任意岗位调用 LLM 动态生成完整的面试模型。"""
    provider = DeepSeekStreamingTextProvider()
    if not provider.api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，无法进行动态岗位分析。")

    company_context = ""
    if company_card:
        company_context = json.dumps(company_card, ensure_ascii=False)[:1200]

    text = jd_text.strip() or _custom_role_seed(job_title)
    mode_hint = _mode_hint_for_dynamic(mode_id)

    user_prompt = f"""
目标岗位：{job_title}
面试模式：{mode_id}（{mode_hint}）
岗位 JD / 参考信息：
{text}

公司情报：
{company_context or "未选择目标公司。"}

请输出完整 JSON。
"""
    try:
        content = await provider.complete_reply(
            [ConversationMessage(role="user", text=user_prompt)],
            system_prompt=DYNAMIC_JOB_SYSTEM_PROMPT,
            temperature=0.0,
        )
        parsed = _parse_json_object(content)
        return _parse_dynamic_model(parsed, job_title=job_title, mode_id=mode_id)
    except Exception as error:
        raise RuntimeError(f"动态岗位分析失败：{error}") from error


def _parse_dynamic_model(payload: dict[str, Any], *, job_title: str, mode_id: str) -> DynamicJobModel:
    """校验并构建 DynamicJobModel，缺失字段自动填充合理默认值。"""
    job_summary = str(payload.get("jobSummary") or _custom_role_seed(job_title)[:120])

    core_requirements = tuple(
        str(item).strip()
        for item in (payload.get("coreRequirements") or payload.get("coreRequirements", []))
        if str(item).strip()
    )[:5] or (_custom_core_requirements(job_title)[:4])

    interview_focus = tuple(
        str(item).strip()
        for item in (payload.get("interviewFocus") or [])
        if str(item).strip()
    )[:5] or (_custom_interview_focus(job_title)[:4])

    # 解析能力维度
    raw_comps = payload.get("competencies") or payload.get("competencies", [])
    if not isinstance(raw_comps, list) or len(raw_comps) < 2:
        raw_comps = _fallback_competencies(job_title)

    competencies: list[DynamicCompetency] = []
    for i, comp in enumerate(raw_comps):
        if not isinstance(comp, dict):
            continue
        cid = str(comp.get("id") or f"comp_{i}")
        cname = str(comp.get("name") or f"能力{i+1}")
        cdesc = str(comp.get("description") or f"{job_title}岗位所需的{cname}")
        cimportance = max(1, min(10, int(comp.get("importance") or comp.get("weight", 5))))
        obs = tuple(str(s).strip() for s in (comp.get("observableSignals") or comp.get("observableSignals", [])) if str(s).strip())[:5]
        weak = tuple(str(s).strip() for s in (comp.get("weakSignals") or comp.get("weakSignals", [])) if str(s).strip())[:5]
        if not obs:
            obs = (f"清楚表达{cname}", f"用具体案例证明{cname}", f"能解释{cname}的判断依据")
        if not weak:
            weak = (f"{cname}描述笼统", f"缺乏{cname}相关证据", f"{cname}与岗位关联弱")
        competencies.append(DynamicCompetency(
            id=cid, name=cname, description=cdesc, weight=cimportance,
            observable_signals=obs, weak_signals=weak,
        ))

    # 从 importance 分数归一化为调度权重（总和 100）
    total_importance = sum(c.weight for c in competencies) or 1
    comp_weights: dict[str, int] = {}
    for c in competencies:
        comp_weights[c.id] = max(3, min(60, round(c.weight / total_importance * 100)))
    # 修正漂移
    drift = 100 - sum(comp_weights.values())
    if comp_weights and drift:
        first_key = next(iter(comp_weights))
        comp_weights[first_key] = max(3, min(60, comp_weights[first_key] + drift))
    focus_id = str(payload.get("focusCompetencyId") or "")
    if focus_id not in comp_weights:
        focus_id = max(comp_weights, key=lambda k: comp_weights[k]) if comp_weights else competencies[0].id if competencies else "comp_0"

    # 证据要求
    raw_ev = payload.get("evidenceRequirements") or payload.get("evidenceRequirements", [])
    if not isinstance(raw_ev, list):
        raw_ev = []
    evidence_requirements: list[tuple[str, tuple[DynamicEvidenceRequirement, ...]]] = []
    for ev_group in raw_ev:
        if not isinstance(ev_group, dict):
            continue
        cid = str(ev_group.get("competencyId") or "")
        if cid not in comp_weights:
            continue
        reqs = ev_group.get("requirements") or ev_group.get("requirements", [])
        if not isinstance(reqs, list):
            continue
        ev_reqs: list[DynamicEvidenceRequirement] = []
        for j, req in enumerate(reqs):
            if not isinstance(req, dict):
                continue
            rid = str(req.get("id") or f"ev_{cid}_{j}")
            rname = str(req.get("name") or f"证据点{j+1}")
            rdesc = str(req.get("description") or f"回答中需要体现：{rname}")
            kws = tuple(str(k).strip() for k in (req.get("keywords") or []) if str(k).strip())[:8]
            if not kws:
                kws = tuple(rname[:3]) if rname else ("证据",)
            ev_reqs.append(DynamicEvidenceRequirement(id=rid, name=rname, description=rdesc, keywords=kws))
        if ev_reqs:
            evidence_requirements.append((cid, tuple(ev_reqs)))

    # 如果某些能力没有证据要求，从 observable_signals 自动生成
    covered_ids = {cid for cid, _ in evidence_requirements}
    for c in competencies:
        if c.id in covered_ids:
            continue
        auto_reqs = tuple(
            DynamicEvidenceRequirement(
                id=f"ev_{c.id}_{i}",
                name=sig,
                description=f"回答中需要体现：{sig}",
                keywords=tuple(sig[:4]) or (sig[:2],),
            )
            for i, sig in enumerate(c.observable_signals[:4])
        )
        if auto_reqs:
            evidence_requirements.append((c.id, auto_reqs))

    # 评分维度
    raw_rubric = payload.get("rubricDimensions") or payload.get("rubricDimensions", [])
    if not isinstance(raw_rubric, list) or len(raw_rubric) < 2:
        raw_rubric = _fallback_rubric(job_title)

    rubric_dimensions: list[DynamicRubricDimension] = []
    for i, dim in enumerate(raw_rubric):
        if not isinstance(dim, dict):
            continue
        did = str(dim.get("id") or f"dim_{i}")
        dname = str(dim.get("name") or f"维度{i+1}")
        ddesc = str(dim.get("description") or f"评价候选人在{dname}方面的表现")
        weak_a = str(dim.get("weakAnchor") or "回答信息散乱，缺少关键证据")
        normal_a = str(dim.get("normalAnchor") or "回答基本完整，但细节或证据不够充分")
        strong_a = str(dim.get("strongAnchor") or "回答清晰、具体、有证据支撑，能回应追问")
        rubric_dimensions.append(DynamicRubricDimension(
            id=did, name=dname, description=ddesc,
            weak_anchor=weak_a, normal_anchor=normal_a, strong_anchor=strong_a,
        ))

    # 提问方式权重
    raw_styles = payload.get("questionStyleWeights") or payload.get("questionStyleWeights", {})
    if isinstance(raw_styles, dict):
        style_weights: dict[str, int] = {}
        for key in ("open", "evidence", "pressure", "relaxed", "reflection"):
            try:
                style_weights[key] = max(0, min(60, int(raw_styles.get(key, 0))))
            except (TypeError, ValueError):
                style_weights[key] = 0
        if sum(style_weights.values()) <= 0:
            style_weights = {"open": 25, "evidence": 35, "pressure": 15, "relaxed": 10, "reflection": 15}
        total_s = sum(style_weights.values())
        style_weights = {k: round(v / total_s * 100) for k, v in style_weights.items()}
        drift_s = 100 - sum(style_weights.values())
        if drift_s:
            first_s = next(iter(style_weights))
            style_weights[first_s] += drift_s
    else:
        style_weights = {"open": 25, "evidence": 35, "pressure": 15, "relaxed": 10, "reflection": 15}

    # 按 mode 修正
    if mode_id == "challenge":
        style_weights["pressure"] = max(style_weights.get("pressure", 15), 30)
    elif mode_id == "guided":
        style_weights["relaxed"] = max(style_weights.get("relaxed", 10), 25)

    focus_style = "evidence" if style_weights.get("evidence", 0) >= style_weights.get("open", 0) else "open"

    # 声音推荐
    voice = _extract_voice(payload.get("recommendedVoice"), mode_id=mode_id, style_weights=style_weights)

    # 种子问题
    seeds = tuple(str(s).strip() for s in (payload.get("questionSeeds") or []) if str(s).strip())[:5]
    if not seeds:
        seeds = (f"请讲一个最能体现你{jobs_title}能力的项目经历。",)

    # 开场问题
    opening = str(payload.get("openingQuestion") or "").strip()
    if not opening or len(opening) > 80:
        opening = f"你好，我们开始{job_title}模拟面试。请先说说你对目标公司和{job_title}岗位的理解。"

    # 分析备注
    notes = tuple(str(n).strip() for n in (payload.get("analysisNotes") or []) if str(n).strip())[:4]

    return DynamicJobModel(
        job_title=job_title,
        job_summary=job_summary,
        core_requirements=core_requirements,
        interview_focus=interview_focus,
        competencies=tuple(competencies),
        question_seeds=seeds,
        competency_weights=comp_weights,
        question_style_weights=style_weights,
        focus_competency_id=focus_id,
        focus_question_style_id=focus_style,
        evidence_requirements=tuple(evidence_requirements),
        rubric_dimensions=tuple(rubric_dimensions),
        recommended_voice=voice,
        analysis_notes=notes,
        analysis_source="deepseek",
        opening_question=opening,
    )


def _dynamic_model_to_payload(model: DynamicJobModel) -> dict[str, object]:
    """将 DynamicJobModel 序列化为前端可传输的 dict。

    competencyWeights 发送 1-10 重要性评分给前端雷达图展示，
    agent 反序列化时会自行归一化为调度权重。
    """
    # 1-10 重要性评分（从 competencies[].weight 提取，用于前端雷达图）
    importance_scores: dict[str, int] = {c.id: c.weight for c in model.competencies}
    return {
        "roleId": "dynamic",
        "roleLabel": model.job_title,
        "jdSummary": model.job_summary,
        "coreRequirements": list(model.core_requirements),
        "interviewFocus": list(model.interview_focus),
        "competencyWeights": importance_scores,
        "questionStyleWeights": model.question_style_weights,
        "focusCompetencyId": model.focus_competency_id,
        "recommendedVoice": model.recommended_voice,
        "analysisNotes": list(model.analysis_notes),
        "analysisSource": model.analysis_source,
        "dynamicModel": {
            "jobTitle": model.job_title,
            "jobSummary": model.job_summary,
            "coreRequirements": list(model.core_requirements),
            "interviewFocus": list(model.interview_focus),
            "competencies": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "weight": c.weight,
                    "observableSignals": list(c.observable_signals),
                    "weakSignals": list(c.weak_signals),
                }
                for c in model.competencies
            ],
            "questionSeeds": list(model.question_seeds),
            "competencyWeights": importance_scores,
            "questionStyleWeights": model.question_style_weights,
            "focusCompetencyId": model.focus_competency_id,
            "evidenceRequirements": [
                {
                    "competencyId": cid,
                    "requirements": [
                        {"id": r.id, "name": r.name, "description": r.description, "keywords": list(r.keywords)}
                        for r in reqs
                    ],
                }
                for cid, reqs in model.evidence_requirements
            ],
            "rubricDimensions": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "weakAnchor": d.weak_anchor,
                    "normalAnchor": d.normal_anchor,
                    "strongAnchor": d.strong_anchor,
                }
                for d in model.rubric_dimensions
            ],
            "recommendedVoice": model.recommended_voice,
            "analysisNotes": list(model.analysis_notes),
            "analysisSource": model.analysis_source,
            "openingQuestion": model.opening_question,
        },
    }


def _extract_voice(raw: object, *, mode_id: str, style_weights: dict[str, int]) -> dict[str, str]:
    allowed_profiles = {"gentle_female_young", "formal_male_adult", "senior_male_calm", "sharp_female_pressure", "friendly_relaxed"}
    allowed_tones = {"encouraging", "formal", "pressure", "relaxed", "calm"}
    result: dict[str, str] = {}
    if isinstance(raw, dict):
        prof = raw.get("voiceProfileId")
        if isinstance(prof, str) and prof in allowed_profiles:
            result["voiceProfileId"] = prof
        tone = raw.get("interviewerTone")
        if isinstance(tone, str) and tone in allowed_tones:
            result["interviewerTone"] = tone
        for key in ("voiceRate", "voicePitch", "voiceVolume"):
            v = raw.get(key)
            if isinstance(v, str) and v.strip():
                result[key] = v.strip()

    if "voiceProfileId" not in result:
        if mode_id == "challenge":
            result["voiceProfileId"] = "sharp_female_pressure"
            result.setdefault("interviewerTone", "pressure")
        else:
            result["voiceProfileId"] = "gentle_female_young"
            result.setdefault("interviewerTone", "encouraging")
    result.setdefault("voiceRate", "+8%")
    result.setdefault("voicePitch", "+2Hz")
    result.setdefault("voiceVolume", "+0%")
    return result


def _fallback_competencies(job_title: str) -> list[dict[str, object]]:
    clean = job_title.strip() or "目标岗位"
    return [
        {
            "id": "comp_0", "name": f"{clean}专业力",
            "description": f"掌握{clean}岗位的核心方法论、工具和流程",
            "importance": 8,
            "observableSignals": ["方法论清晰", "工具使用具体", "流程管理规范", "专业判断有依据"],
            "weakSignals": ["方法论含糊", "靠直觉而非方法", "流程意识弱"],
        },
        {
            "id": "comp_1", "name": "业务理解",
            "description": f"理解公司业务、用户/客户需求、行业趋势和岗位价值",
            "importance": 7,
            "observableSignals": ["理解业务目标", "知道用户/客户价值", "能连接行业趋势", "动机可信"],
            "weakSignals": ["只讲任务执行", "不了解业务场景", "行业意识弱"],
        },
        {
            "id": "comp_2", "name": "问题分析与判断",
            "description": "能拆解复杂问题，识别关键变量、约束条件和取舍逻辑",
            "importance": 7,
            "observableSignals": ["问题定义清楚", "拆解逻辑合理", "约束识别准确", "判断有据"],
            "weakSignals": ["问题描述笼统", "缺少拆解", "忽略约束"],
        },
        {
            "id": "comp_3", "name": "执行与协作",
            "description": "能推动落地、跨团队协作、处理风险和冲突",
            "importance": 6,
            "observableSignals": ["个人角色明确", "关键动作具体", "协作对象清楚", "风险有预案"],
            "weakSignals": ["角色模糊", "推进过程一笔带过", "协作描述空泛"],
        },
        {
            "id": "comp_4", "name": "结果与复盘",
            "description": "能用数据、反馈或前后对比证明成果，并复盘改进",
            "importance": 5,
            "observableSignals": ["有量化结果", "能解释归因", "知道业务影响", "复盘具体"],
            "weakSignals": ["只说做完", "没有指标", "结果与行动脱节", "缺少反思"],
        },
    ]


def _fallback_rubric(job_title: str) -> list[dict[str, object]]:
    clean = job_title.strip() or "目标岗位"
    return [
        {
            "id": "dim_0", "name": f"{clean}专业能力",
            "description": f"是否体现{clean}岗位所需的核心方法和判断力",
            "weakAnchor": "描述笼统，缺乏专业方法和对岗位的理解",
            "normalAnchor": "有基本专业意识，但方法和判断不够具体",
            "strongAnchor": "能清晰展示专业方法、判断依据和岗位匹配度",
        },
        {
            "id": "dim_1", "name": "经历证据",
            "description": "是否用细节、数据、场景或反馈证明自己的贡献",
            "weakAnchor": "泛泛描述，缺少可验证证据和个人贡献",
            "normalAnchor": "有部分细节或结果，但证据链不完整",
            "strongAnchor": "能给出具体行动、数据变化、用户反馈或前后对比",
        },
        {
            "id": "dim_2", "name": "回答结构",
            "description": "回答是否有清晰的背景、目标、行动、结果和反思",
            "weakAnchor": "信息散乱，只是在罗列经历，听不出主线",
            "normalAnchor": "有基本结构，但重点、因果和转折不够突出",
            "strongAnchor": "能在有限时间内清楚说明背景、目标、行动、结果和反思",
        },
        {
            "id": "dim_3", "name": "业务理解",
            "description": "是否体现对公司业务、用户场景和岗位价值的理解",
            "weakAnchor": "更像执行任务，没有体现业务判断和用户意识",
            "normalAnchor": "能体现部分业务意识，但和目标岗位连接不够稳定",
            "strongAnchor": "能把项目经历和目标公司/岗位的业务价值自然连接",
        },
        {
            "id": "dim_4", "name": "表达与临场",
            "description": "表达是否自然、简洁、稳定，追问下是否能保持逻辑",
            "weakAnchor": "表达绕、虚或不稳定，追问后容易失焦",
            "normalAnchor": "表达基本清楚，但重点和节奏还可以更稳定",
            "strongAnchor": "表达具体、自然、有重点，追问下仍能稳定补充",
        },
    ]


def _mode_hint_for_dynamic(mode_id: str) -> str:
    return {
        "standard": "接近真实结构化面试，专业且有适当压力",
        "guided": "更温和鼓励，给方向提示但不替候选人作答",
        "challenge": "更尖锐直接，重点挑战证据、逻辑和边界",
    }.get(mode_id, "标准结构化面试")


async def analyze_jd_with_llm(
    *,
    role_id: str,
    role_label: str = "",
    mode_id: str = "standard",
    jd_text: str = "",
    company_card: dict[str, Any] | None = None,
) -> dict[str, object]:
    role = role_by_id(role_id)
    display_role = role_label.strip() or role.label
    custom_seed_text = _custom_role_seed(display_role) if display_role != role.label else ""

    # 所有岗位统一走动态 LLM 分析，预设模板仅作 fallback
    try:
        model = await analyze_dynamic_job(
            job_title=display_role or "目标岗位",
            mode_id=mode_id,
            jd_text=jd_text or custom_seed_text,
            company_card=company_card,
        )
        return _dynamic_model_to_payload(model)
    except RuntimeError:
        # LLM 失败，回退到规则引擎
        pass

    # LLM 失败 → 规则引擎兜底（用配置模板转 dynamic model 保证格式统一）
    fallback_model = _fallback_dynamic_model(
        job_title=display_role, role_id=role_id, mode_id=mode_id,
        jd_text=jd_text or custom_seed_text, company_card=company_card,
    )
    return _dynamic_model_to_payload(fallback_model)


def _fallback_dynamic_model(
    *,
    job_title: str,
    role_id: str,
    mode_id: str,
    jd_text: str = "",
    company_card: dict[str, Any] | None = None,
) -> DynamicJobModel:
    """LLM 不可用时，从预设模板 + 规则构建 DynamicJobModel 作为兜底。"""
    from interview.configs import role_template_to_dynamic_model

    role = role_by_id(role_id)
    model = role_template_to_dynamic_model(role)

    # 如果是自定义岗位名（不匹配预设），覆盖 job_title
    if job_title and job_title != role.label:
        overrides: dict[str, object] = {"job_title": job_title}
    else:
        overrides = {}

    # 根据 mode 调整 question_style_weights
    style_weights = dict(model.question_style_weights)
    if mode_id == "challenge":
        style_weights.update({"open": 15, "evidence": 30, "pressure": 35, "relaxed": 5, "reflection": 15})
    elif mode_id == "guided":
        style_weights.update({"open": 35, "evidence": 25, "pressure": 5, "relaxed": 20, "reflection": 15})

    # 根据 mode 调整 recommended_voice
    voice = dict(model.recommended_voice)
    if mode_id == "challenge":
        voice.update({"voiceProfileId": "sharp_female_pressure", "interviewerTone": "pressure"})
    elif mode_id == "guided":
        voice.update({"voiceProfileId": "gentle_female_young", "interviewerTone": "encouraging"})

    return DynamicJobModel(
        job_title=job_title or model.job_title,
        job_summary=jd_text[:120] if jd_text else model.job_summary,
        core_requirements=model.core_requirements,
        interview_focus=model.interview_focus,
        competencies=model.competencies,
        question_seeds=model.question_seeds,
        competency_weights=model.competency_weights,
        question_style_weights=style_weights,
        focus_competency_id=model.focus_competency_id,
        focus_question_style_id=model.focus_question_style_id,
        evidence_requirements=model.evidence_requirements,
        rubric_dimensions=model.rubric_dimensions,
        recommended_voice=voice,
        analysis_notes=("LLM 不可用，使用预设模板配置。建议检查 DeepSeek API Key 和网络。",),
        analysis_source="template_fallback",
        opening_question=model.opening_question,
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?", "", clean).strip()
        clean = re.sub(r"```$", "", clean).strip()
    match = re.search(r"\{.*\}", clean, flags=re.S)
    if match:
        clean = match.group(0)
    payload = json.loads(clean)
    return payload if isinstance(payload, dict) else {}


def _merge_llm_payload(fallback: dict[str, object], payload: dict[str, Any]) -> dict[str, object]:
    required_fields = ("jdSummary", "coreRequirements", "interviewFocus", "competencyWeights", "questionStyleWeights")
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise RuntimeError(f"DeepSeek JD 分析缺少必要字段：{', '.join(missing_fields)}")
    if not isinstance(payload.get("competencyWeights"), dict) or not isinstance(payload.get("questionStyleWeights"), dict):
        raise RuntimeError("DeepSeek JD 分析返回的雷达权重格式不正确。")

    result = dict(fallback)
    result["jdSummary"] = str(payload.get("jdSummary") or "").strip()
    result["coreRequirements"] = _string_list(payload.get("coreRequirements"), limit=5)
    result["interviewFocus"] = _string_list(payload.get("interviewFocus"), limit=5)
    if not result["jdSummary"] or not result["coreRequirements"] or not result["interviewFocus"]:
        raise RuntimeError("DeepSeek JD 分析返回内容为空，无法生成真实配置。")
    result["analysisNotes"] = _string_list(payload.get("analysisNotes"), limit=5)
    result["competencyWeights"] = _normalize_weights(
        payload.get("competencyWeights"),
        fallback.get("competencyWeights", {}),
        allowed={
            "role_core",
            "business_understanding",
            "problem_analysis",
            "execution_delivery",
            "data_impact",
            "communication_reflection",
        },
    )
    result["questionStyleWeights"] = _normalize_weights(
        payload.get("questionStyleWeights"),
        fallback.get("questionStyleWeights", {}),
        allowed={"open", "evidence", "pressure", "relaxed", "reflection"},
    )
    focus_competency_id = str(payload.get("focusCompetencyId") or "")
    competency_weights = result["competencyWeights"]
    if not isinstance(competency_weights, dict):
        competency_weights = {}
    if focus_competency_id not in competency_weights and competency_weights:
        focus_competency_id = max(competency_weights, key=lambda key: int(competency_weights[key]))
    result["focusCompetencyId"] = focus_competency_id or fallback.get("focusCompetencyId", "role_core")
    result["recommendedVoice"] = _merge_recommended_voice(
        fallback.get("recommendedVoice", {}),
        payload.get("recommendedVoice"),
    )
    result["analysisSource"] = "deepseek"
    return result


def _merge_recommended_voice(fallback: object, raw: object) -> dict[str, str]:
    allowed_profiles = {
        "gentle_female_young",
        "formal_male_adult",
        "senior_male_calm",
        "sharp_female_pressure",
        "friendly_relaxed",
    }
    allowed_tones = {"encouraging", "formal", "pressure", "relaxed", "calm"}
    result = dict(fallback) if isinstance(fallback, dict) else {}
    if isinstance(raw, dict):
        profile = raw.get("voiceProfileId")
        if isinstance(profile, str) and profile in allowed_profiles:
            result["voiceProfileId"] = profile
        tone = raw.get("interviewerTone")
        if isinstance(tone, str) and tone in allowed_tones:
            result["interviewerTone"] = tone
        for key in ("voiceRate", "voicePitch", "voiceVolume"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                result[key] = value.strip()
    return {str(key): str(value) for key, value in result.items() if value is not None}


def _normalize_weights(raw: object, fallback: object, *, allowed: set[str]) -> dict[str, int]:
    source = raw if isinstance(raw, dict) else fallback
    weights: dict[str, int] = {}
    if isinstance(source, dict):
        for key in allowed:
            try:
                weights[key] = max(0, int(float(source.get(key, 0))))
            except (TypeError, ValueError):
                weights[key] = 0
    if not weights or sum(weights.values()) <= 0:
        return {key: round(100 / len(allowed)) for key in allowed}
    total = sum(weights.values())
    normalized = {key: round(value / total * 100) for key, value in weights.items()}
    drift = 100 - sum(normalized.values())
    first = next(iter(normalized))
    normalized[first] += drift
    return normalized


def _string_list(raw: object, *, limit: int) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw[:limit] if str(item).strip()]


def _summary_for(role_label: str, text: str) -> str:
    if not text:
        return f"未提供具体 JD，已使用{role_label}通用岗位模型。"
    clean = text.replace("\n", " ").strip()
    return f"已基于 JD 文本分析{role_label}面试重点：{clean[:180]}{'...' if len(clean) > 180 else ''}"


def _custom_role_seed(role_label: str) -> str:
    clean = role_label.strip() or "目标岗位"
    return (
        f"{clean}岗位通常需要理解岗位职责、业务场景、核心能力要求、协作对象和结果指标。"
        f"面试会重点考察候选人是否理解{clean}的工作目标、关键任务、问题拆解方式、"
        "过往经历匹配度、落地执行能力、数据结果意识和复盘反思能力。"
    )


def _custom_core_requirements(role_label: str) -> list[str]:
    clean = role_label.strip() or "目标岗位"
    return [
        f"能清楚说明{clean}的核心职责、服务对象和业务目标。",
        f"能把自己的项目经历与{clean}需要的能力建立直接连接。",
        "能拆解真实业务问题，说明判断依据、约束条件和取舍逻辑。",
        "能展示推进落地、跨团队协作、风险处理和结果复盘能力。",
        "能用指标、反馈或前后对比证明自己的贡献和岗位匹配度。",
    ]


def _custom_interview_focus(role_label: str) -> list[str]:
    clean = role_label.strip() or "目标岗位"
    return [
        f"追问候选人对{clean}岗位职责和工作场景的理解是否具体。",
        "追问过往经历中最能证明岗位匹配度的项目、动作和结果。",
        "追问问题拆解、关键取舍、协作推进和风险处理的细节。",
        "追问结果指标、业务影响、复盘反思和下一步优化思路。",
        "追问候选人为什么适合该岗位，以及进入目标公司后的价值判断。",
    ]


def _core_requirements_for(role_id: str) -> list[str]:
    mapping = {
        "product_manager": [
            "能把用户问题、业务目标和产品方案连接起来，而不是只描述功能。",
            "能说明需求优先级、取舍依据、验证方式和上线后的复盘闭环。",
            "能推动设计、研发、运营等多方协作，并处理冲突和风险。",
            "能用数据、用户反馈或业务指标证明产品动作的价值。",
        ],
        "operations": [
            "能围绕用户增长、转化或留存设计清晰的运营策略。",
            "能拆解活动、内容、社群或渠道的执行链路和资源协同。",
            "能通过指标复盘运营效果，识别归因边界和下一步优化。",
            "能把用户动机、平台规则和商业目标结合起来表达。",
        ],
        "data_analyst": [
            "能把业务问题拆成假设、指标、口径、样本和分析方法。",
            "能说明 SQL/Python/BI 等工具如何服务于具体业务判断。",
            "能处理数据质量、口径争议、归因边界和结论可信度。",
            "能把分析结论转化为业务建议，并推动决策或行动。",
        ],
        "frontend_engineer": [
            "能说明组件设计、状态管理、交互实现和工程质量的取舍。",
            "能定位复杂联调、性能、异常和用户体验问题。",
            "能和产品、设计、后端协作，保证接口边界和上线质量。",
            "能用性能指标、质量指标或体验反馈证明工程改进效果。",
        ],
    }
    return mapping.get(role_id, mapping["product_manager"])


def _interview_focus_for(role_id: str) -> list[str]:
    mapping = {
        "product_manager": [
            "追问候选人如何定义真实需求，以及有没有验证用户痛点。",
            "追问方案取舍、优先级排序和跨团队推进中的具体冲突。",
            "追问上线后的结果指标、归因判断和复盘改进。",
            "追问候选人对目标公司业务场景和岗位价值的理解。",
        ],
        "operations": [
            "追问运营目标如何设定，用户分层和转化链路是否清楚。",
            "追问活动/内容/社群执行中的资源协调和节奏控制。",
            "追问数据复盘是否能解释真实原因，而不是只报结果。",
            "追问失败案例、策略调整和下一轮优化动作。",
        ],
        "data_analyst": [
            "追问业务问题是否被拆成可验证假设和清晰指标。",
            "追问数据口径、样本选择、对比方法和分析边界。",
            "追问结论如何影响业务决策，以及是否有后续验证。",
            "追问被质疑时如何解释方法局限和结论可信度。",
        ],
        "frontend_engineer": [
            "追问复杂项目中的技术方案、状态边界和组件设计。",
            "追问性能优化、异常处理和用户体验改进的量化结果。",
            "追问跨端、联调、上线风险和协作冲突处理。",
            "追问工程复盘、可维护性和测试/质量保障意识。",
        ],
    }
    return mapping.get(role_id, mapping["product_manager"])


def _analysis_notes(role_label: str, hits: dict[str, int]) -> list[str]:
    strongest = sorted(hits.items(), key=lambda item: item[1], reverse=True)[:3]
    return [
        f"{role_label}岗位能力模型已固定为 6 维，JD 只调整权重，不改变评价体系。",
        "命中关键词较多的维度会提高面试追问优先级。",
        f"当前重点维度：{', '.join(key for key, value in strongest if value > 0) or '使用默认权重'}。",
    ]


def _recommended_voice(role_id: str, question_style_weights: dict[str, int]) -> dict[str, str]:
    if question_style_weights.get("pressure", 0) >= 20:
        return {
            "voiceProfileId": "sharp_female_pressure",
            "interviewerTone": "pressure",
            "voiceRate": "+10%",
            "voicePitch": "+2Hz",
            "voiceVolume": "+0%",
        }
    if role_id in {"data_analyst", "frontend_engineer"}:
        return {
            "voiceProfileId": "formal_male_adult",
            "interviewerTone": "formal",
            "voiceRate": "+6%",
            "voicePitch": "-2Hz",
            "voiceVolume": "+0%",
        }
    return {
        "voiceProfileId": "gentle_female_young",
        "interviewerTone": "encouraging",
        "voiceRate": "+8%",
        "voicePitch": "+2Hz",
        "voiceVolume": "+0%",
    }


def _blend_weights(base: dict[str, int], profile: dict[str, int], *, ratio: float) -> dict[str, int]:
    keys = set(base) | set(profile)
    blended = {key: round(base.get(key, 0) * (1 - ratio) + profile.get(key, 0) * ratio) for key in keys}
    total = sum(blended.values()) or 1
    normalized = {key: round(value / total * 100) for key, value in blended.items()}
    drift = 100 - sum(normalized.values())
    if normalized:
        first = next(iter(normalized))
        normalized[first] += drift
    return normalized


def _apply_mode_to_fallback(payload: dict[str, object], mode_id: str) -> dict[str, object]:
    result = dict(payload)
    styles = dict(result.get("questionStyleWeights") if isinstance(result.get("questionStyleWeights"), dict) else {})
    if mode_id == "challenge":
        styles.update({"open": 15, "evidence": 30, "pressure": 35, "relaxed": 5, "reflection": 15})
        result["recommendedVoice"] = {
            "voiceProfileId": "sharp_female_pressure",
            "interviewerTone": "pressure",
            "voiceRate": "+10%",
            "voicePitch": "+2Hz",
            "voiceVolume": "+0%",
        }
    elif mode_id == "guided":
        styles.update({"open": 35, "evidence": 25, "pressure": 5, "relaxed": 20, "reflection": 15})
        result["recommendedVoice"] = {
            "voiceProfileId": "gentle_female_young",
            "interviewerTone": "encouraging",
            "voiceRate": "+8%",
            "voicePitch": "+2Hz",
            "voiceVolume": "+0%",
        }
    result["questionStyleWeights"] = styles
    return result
