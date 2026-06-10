from collections import Counter

from interview.configs import (
    CAPABILITY_TRACKS,
    MODE_BEHAVIOR,
    PRODUCT_MANAGER_OPENING,
    RUBRIC_DIMENSIONS,
    STRATEGY_FOCUS,
    role_by_id,
    voice_profile_by_id,
)
from interview.models import (
    CapabilityTrack,
    CompanyIntelligenceCard,
    DynamicEvidenceRequirement,
    DynamicJobModel,
    EvidenceRequirement,
    InterviewState,
    InterviewTurn,
)


QUESTION_STYLE_BEHAVIOR = {
    "open": "当前问题类型：开放提问。用较开放的问题让候选人展开，但仍然要围绕当前能力。",
    "evidence": "当前问题类型：证据追问。必须追问具体数据、细节、个人贡献或前后对比。",
    "pressure": "当前问题类型：压力追问。问题要更短、更直接，挑战逻辑漏洞或证据不足，但不得攻击候选人。",
    "relaxed": "当前问题类型：轻松提问。语气自然，帮助候选人补充背景和思路，但不能替他作答。",
    "reflection": "当前问题类型：复盘提问。重点追问取舍、失败、反思和如果重做会怎么改。",
}


class InterviewOrchestrator:
    def __init__(self) -> None:
        self.state = InterviewState(last_question=PRODUCT_MANAGER_OPENING)

    @property
    def has_dynamic_model(self) -> bool:
        return self.state.dynamic_model is not None

    @property
    def _model(self) -> DynamicJobModel | None:
        return self.state.dynamic_model

    @property
    def opening_question(self) -> str:
        return self.state.last_question or PRODUCT_MANAGER_OPENING

    @property
    def turns(self) -> list[InterviewTurn]:
        return self.state.turns

    @property
    def should_finish(self) -> bool:
        if self.state.candidate_turn_count >= self.state.max_candidate_turns:
            return True
        if self.state.candidate_turn_count < self.state.min_candidate_turns:
            return False
        return self.coverage_ratio() >= 0.72 and self._covered_track_count() >= 2

    def reset(self) -> None:
        self.state = InterviewState(last_question=PRODUCT_MANAGER_OPENING)

    def configure(
        self,
        *,
        job_id: str = "product_manager",
        job_label: str = "",
        mode_id: str = "standard",
        competency_id: str = "requirement_analysis",
        strategy_id: str = "evidence_probe",
        followup_mode: str = "fast",
        company_card: CompanyIntelligenceCard | None = None,
        jd_text: str = "",
        resume_text: str = "",
        voice_profile_id: str = "gentle_female_young",
        voice_rate: str = "",
        voice_pitch: str = "",
        voice_volume: str = "",
        interviewer_tone: str = "encouraging",
        competency_weights: dict[str, int] | None = None,
        question_style_weights: dict[str, int] | None = None,
        dynamic_model: DynamicJobModel | None = None,
    ) -> None:
        if dynamic_model:
            # 使用 AI 动态生成的岗位模型
            comp_weights = competency_weights or dynamic_model.competency_weights
            style_weights = question_style_weights or dynamic_model.question_style_weights
            first_comp = dynamic_model.competencies[0] if dynamic_model.competencies else None
            self.state = InterviewState(
                job_name=dynamic_model.job_title,
                job_id="dynamic",
                scenario=f"{first_comp.name}深化" if first_comp else "综合面试",
                mode_id=mode_id,
                competency_id=dynamic_model.focus_competency_id or (first_comp.id if first_comp else "comp_0"),
                strategy_id=strategy_id,
                followup_mode=followup_mode,
                company_card=company_card,
                jd_text=jd_text.strip(),
                resume_text=resume_text.strip(),
                voice_profile_id=voice_profile_id,
                voice_rate=voice_rate,
                voice_pitch=voice_pitch,
                voice_volume=voice_volume,
                interviewer_tone=interviewer_tone,
                competency_weights=comp_weights,
                question_style_weights=style_weights,
                current_capability_id=dynamic_model.focus_competency_id or (first_comp.id if first_comp else "comp_0"),
                current_question_style_id="open",
                last_question="",
                dynamic_model=dynamic_model,
            )
            self.state.last_question = dynamic_model.opening_question or self._opening_question_for(
                dynamic_model.focus_competency_id, strategy_id, company_card
            )
        else:
            role = role_by_id(job_id)
            competency = competency_id if any(item.id == competency_id for item in role.competencies) else role.competencies[0].id
            competency_name = next((item.name for item in role.competencies if item.id == competency), "项目经历")
            self.state = InterviewState(
                job_name=job_label.strip() or role.label,
                job_id=role.id,
                scenario=f"{competency_name}深化",
                mode_id=mode_id,
                competency_id=competency,
                strategy_id=strategy_id,
                followup_mode=followup_mode,
                company_card=company_card,
                jd_text=jd_text.strip(),
                resume_text=resume_text.strip(),
                voice_profile_id=voice_profile_id,
                voice_rate=voice_rate,
                voice_pitch=voice_pitch,
                voice_volume=voice_volume,
                interviewer_tone=interviewer_tone,
                competency_weights=competency_weights or self._default_competency_weights(role.id),
                question_style_weights=question_style_weights or {},
                current_capability_id=competency,
                current_question_style_id="open",
                last_question="",
                dynamic_model=None,
            )
            self.state.last_question = self._opening_question_for(competency, strategy_id, company_card)

    def record_candidate_answer(self, answer: str) -> None:
        self.state.turns.append(
            InterviewTurn(
                question=self.state.last_question,
                answer=answer.strip(),
                capability_id=self.state.current_capability_id,
                question_style_id=self.state.current_question_style_id,
            )
        )
        self.state.current_capability_id = self._next_capability_id()
        self.state.current_question_style_id = self._next_question_style_id()

    def record_assistant_question(self, question: str) -> None:
        self.state.last_question = question.strip()

    def closing_text(self) -> str:
        return "本轮面试已结束，报告已生成。"

    def coverage_ratio(self) -> float:
        tracks = self._active_tracks()
        total = sum(len(track.requirements) for track in tracks)
        if total == 0:
            return 0.0
        covered = sum(1 for track in tracks for requirement in track.requirements if self._requirement_present(requirement.keywords))
        return covered / total

    def build_question_trace(self) -> dict[str, object]:
        current_track = self.current_track()
        missing_requirements = list(self.current_missing_evidence())
        style_id = self.state.current_question_style_id or "open"
        competency_weight = (self.state.competency_weights or {}).get(current_track.id, 0)
        style_weight = (self.state.question_style_weights or {}).get(style_id, 0)
        return {
            "capabilityId": current_track.id,
            "capabilityName": current_track.name,
            "capabilityDescription": current_track.description,
            "capabilityWeight": competency_weight,
            "questionStyleId": style_id,
            "questionStyleName": self._question_style_name(style_id),
            "questionStyleWeight": style_weight,
            "coverageRatio": round(self._track_coverage(current_track), 2),
            "missingEvidence": missing_requirements,
            "traceReason": self._question_trace_reason(current_track, style_id, missing_requirements),
            "turnIndex": self.state.candidate_turn_count + 1,
        }

    def current_track(self) -> CapabilityTrack:
        return self._track_by_id(self.state.current_capability_id) or self._active_tracks()[0]

    def current_missing_evidence(self) -> tuple[str, ...]:
        current_track = self.current_track()
        return tuple(
            item.name for item in current_track.requirements if not self._requirement_present(item.keywords)
        )

    def current_interview_style_id(self) -> str:
        if self.state.interviewer_tone == "pressure" or self.state.mode_id == "pressure":
            return "pressure"
        if self.state.interviewer_tone == "formal":
            return "formal"
        if self.state.interviewer_tone in {"relaxed", "encouraging"}:
            return "supportive"
        if self.state.candidate_turn_count >= max(8, self.state.max_candidate_turns - 3):
            return "final_round"
        return "standard"

    def record_professional_followup_trace(self, payload: dict[str, object]) -> None:
        self.state.professional_question_traces.append(payload)
        strategy_id = str(payload.get("selectedStrategyId", "")).strip()
        if strategy_id:
            self.state.recent_strategy_ids.append(strategy_id)
            self.state.recent_strategy_ids = self.state.recent_strategy_ids[-6:]
        gap_types = payload.get("answerGapTypes")
        if isinstance(gap_types, list):
            self.state.last_answer_gap = {
                "gapTypes": gap_types,
                "confidence": payload.get("answerGapConfidence", 0),
                "summary": payload.get("answerQualitySummary", ""),
                "bestNextProbeTarget": payload.get("bestNextProbeTarget", ""),
            }

    def build_followup_prompt(self) -> str:
        current_track = self._track_by_id(self.state.current_capability_id) or self._active_tracks()[0]
        voice_profile = voice_profile_by_id(self.state.voice_profile_id)
        asked_turns = "\n".join(
            f"Q{i + 1}: {turn.question}\nA{i + 1}: {turn.answer}" for i, turn in enumerate(self.state.turns)
        )
        requirements = "\n".join(
            f"- {item.name}: {item.description}（当前状态：{'已出现' if self._requirement_present(item.keywords) else '待采集'}）"
            for item in current_track.requirements
        )
        all_tracks = "\n".join(f"- {track.name}: {track.description}" for track in self._active_tracks())
        company_context = self._company_context_text()
        if self._model:
            jd_context = self.state.jd_text[:900] or self._model.job_summary
            role_label = self._model.job_title
        else:
            role = role_by_id(self.state.job_id)
            jd_context = self.state.jd_text[:900] or role.generic_jd
            role_label = role.label
        resume_context = self.state.resume_text[:1200] or "用户未提供简历，追问时只能基于现场回答。"
        style_weights = ", ".join(f"{key}:{value}%" for key, value in self.state.question_style_weights.items()) or "使用默认提问方式占比"
        current_style = self.state.current_question_style_id or "open"
        current_style_behavior = QUESTION_STYLE_BEHAVIOR.get(current_style, QUESTION_STYLE_BEHAVIOR["open"])

        last_answer = self.state.turns[-1].answer if self.state.turns else ""

        return f"""
你是一个面向应届生的公司岗位级 AI 面试训练教练，正在做结构化语音模拟面试。

当前面试：
- 岗位：{self.state.job_name}
- 通用 JD / JD 覆盖：{jd_context}
- 场景：{self.state.scenario}
- 已完成候选人回答轮次：{self.state.candidate_turn_count}
- 最少轮次：{self.state.min_candidate_turns}
- 上限轮次：{self.state.max_candidate_turns}
- 模式：{MODE_BEHAVIOR.get(self.state.mode_id, MODE_BEHAVIOR["standard"])}
- 追问方式：{STRATEGY_FOCUS.get(self.state.strategy_id, STRATEGY_FOCUS["evidence_probe"])}
- 提问方式占比：{style_weights}
- 本轮必须体现的提问方式：{current_style}；{current_style_behavior}
- 面试官语气：{self._interviewer_tone_prompt(voice_profile.interviewer_style_prompt)}

公司情报：
{company_context}

简历资料：
{resume_context}

整体能力轨道：
{all_tracks}

当前优先采证能力：{current_track.name}
当前能力的证据要求：
{requirements}

候选人刚才的回答：
{last_answer}

已经发生的对话：
{asked_turns}

追问原则：
- 每次只问一个问题。
- 必须基于候选人上一轮回答继续追问。
- 下一问必须包含或指向候选人刚才回答里的具体信息，不允许自说自话。
- 如果候选人回答提到公司、岗位或简历内容，必须优先沿着这些真实内容追问。
- 如果公司资料是待核验，不要编造公司事实，只能追问候选人理解和准备思路。
- 优先补齐当前能力中“待采集”的证据。
- 如果当前能力已较充分，就自然切到下一条能力轨道。
- 不要连续两轮纠缠同一个缺失点。
- 必须明显体现当前模式和追问方式，不能所有模式都问成同一种语气。
- 本轮问题必须符合“本轮必须体现的提问方式”，让用户能感知到配置变化。
- 不要输出评分、分析、Markdown 或解释。
- 回复中文，控制在 60 个汉字以内，适合语音播报。
""".strip()

    def build_evaluation_prompt(self) -> str:
        transcript = "\n".join(
            f"面试官：{turn.question}\n候选人：{turn.answer}\n考察能力：{self._track_name(turn.capability_id)}\n提问方式：{turn.question_style_id}"
            for turn in self.state.turns
        )
        # 使用动态评分维度或默认 RUBRIC_DIMENSIONS
        if self._model:
            rubric_dims = self._model.rubric_dimensions
            role_label = self._model.job_title
            jd_context = self.state.jd_text[:900] or self._model.job_summary
        else:
            role = role_by_id(self.state.job_id)
            rubric_dims = RUBRIC_DIMENSIONS
            role_label = role.label
            jd_context = self.state.jd_text[:900] or role.generic_jd
        rubric = "\n".join(
            f"- {item.id}/{item.name}: {item.description}；2分：{item.weak_anchor}；6分：{item.normal_anchor}；9-10分：{item.strong_anchor}"
            for item in rubric_dims
        )
        evidence_snapshot = self.evidence_snapshot_text()
        question_trace_snapshot = self.question_trace_snapshot_text()
        company_context = self._company_context_text()

        return f"""
你是 AI 求职训练产品的结构化面试复盘教练。
请基于“对话原文 + 证据采集状态 + 行为锚定评分标准”生成报告。

重要要求：
- 你是“训练教练”，不是“淘汰面试官”。报告要真实指出问题，但语气必须帮助用户知道下一步怎么变好，避免全盘否定。
- summary 必须先写 1 个可以保留的有效表现，再写 1 个最需要提升的问题；不要只输出负面结论。
- 如果证据不足，要明确说“暂不能稳定判断”，不要把证据不足直接等同于能力差。
- 低分必须谨慎：1-2 分只用于几乎没有相关回答或严重自相矛盾；3-4 分用于有明显尝试但证据链断裂；如果候选人给出了基本完整经历，通常不应低于 5。
- 评分基准：5-6 是“当前可训练、基本能用但证据不足”；7-8 是“有清楚结构和可验证证据”；9-10 是“接近优秀面试表现”。不要因为答案不完美就压到 2-3 分。
- 每个维度都要同时写“已看到的信号”和“下一步补强点”；如果某维度信息不足，reason 中写清缺失，不要写成人格化否定。
- 公司信息如果是待核验，只评价候选人的准备意识、岗位连接和表达质量，不要评价未知事实真假。
- 不要用模板化空话。
- 每个分数必须能对应候选人回答中的具体证据或明确缺失项。
- 公司理解和岗位匹配必须单独评价，不能混在 summary 里一笔带过。
- 训练计划必须基于本轮证据缺口，给出 7 天、14 天、30 天三个阶段的训练重点。
- 训练计划要体系化、具体、可执行，但不要幻想不存在的经历。
- 分数范围是 1-10，不能输出 0 分。

评分维度：
{rubric}

目标岗位：
- 岗位：{self.state.job_name}
- 通用 JD：{jd_context}
- JD 覆盖：{self.state.jd_text[:900] or "无"}

公司情报：
{company_context}

简历资料：
{self.state.resume_text[:1200] or "用户未提供简历。"}

证据采集状态：
{evidence_snapshot}

追问计划轨迹：
{question_trace_snapshot}

对话记录：
{transcript}

只输出 JSON，结构如下：
{{
  "report_quality": "full",
  "summary": "整体表现总结：先说明一个可保留的有效表现，再说明一个最需要提升的问题",
  "ability_model": {{
    // 每个评分维度一个分数，维度 ID 见上方评分维度列表
    "dim_0": 6,
    "dim_1": 5,
    "dim_2": 6,
    "dim_3": 5,
    "dim_4": 6
  }},
  "dimensions": [
    {{
      "id": "评分维度ID（上方评分维度中列出的ID）",
      "name": "维度名称",
      "score": 6,
      "level": "待补强/基础可用/较好/优秀",
      "reason": "已看到的有效信号 + 为什么还没有到下一档",
      "evidence": "引用或概括候选人回答中的具体依据；如果没有就写缺失",
      "risk": "真实面试中可能被质疑的问题",
      "improvement": "提升到下一档需要补什么"
    }}
  ],
  "evidence_gaps": ["还缺哪些关键证据"],
  "company_fit_bonus": {{
    "score": 6,
    "reason": "候选人对公司理解和岗位连接的表现",
    "verification_note": "公司资料是否已核验",
    "talking_points": ["候选人可以继续准备的公司/业务话题"]
  }},
  "role_fit": {{
    "score": 6,
    "reason": "候选人与目标岗位能力模型的匹配程度",
    "focus_dimensions": ["最相关的岗位能力维度"],
    "risk": "真实面试中可能暴露的岗位匹配风险"
  }},
  "main_weakness": "当前最优先补强点，使用可行动表述，避免否定人格或能力上限",
  "training_plan": {{
    "theme": "下一阶段训练主题",
    "goal": "训练目标",
    "duration_minutes": 15,
    "seven_day_plan": ["7天内的训练重点"],
    "fourteen_day_plan": ["14天内的训练重点"],
    "thirty_day_plan": ["30天内的训练重点"],
    "tasks": [
      {{
        "name": "训练任务名",
        "exercise": "具体练习题",
        "method": "怎么练",
        "success_criteria": "达标标准"
      }}
    ],
    "next_interview_focus": "下一轮模拟面试重点"
  }}
}}
""".strip()

    def evidence_snapshot_text(self) -> str:
        lines: list[str] = []
        for track in self._active_tracks():
            lines.append(f"{track.name}:")
            for requirement in track.requirements:
                status = "已出现" if self._requirement_present(requirement.keywords) else "缺失"
                lines.append(f"- {requirement.name}: {status}")
        return "\n".join(lines)

    def question_trace_snapshot_text(self) -> str:
        lines: list[str] = []
        for index, turn in enumerate(self.state.turns, start=1):
            lines.append(
                f"第{index}轮：能力={self._track_name(turn.capability_id)}；提问方式={self._question_style_name(turn.question_style_id)}；问题={turn.question}"
            )
        for trace in self.state.professional_question_traces:
            gap = ", ".join(str(item) for item in trace.get("answerGapTypes", []) or [])
            sources = ", ".join(str(item) for item in trace.get("ragSourceTitles", []) or [])
            lines.append(
                f"专业追问计划：策略={trace.get('selectedStrategyId', '')}；缺口={gap or '无'}；RAG={sources or '未命中'}"
            )
        return "\n".join(lines) or "暂无追问轨迹。"

    def total_answer_chars(self) -> int:
        return sum(len(turn.answer.strip()) for turn in self.state.turns)

    def is_sample_insufficient(self) -> bool:
        return self.state.candidate_turn_count < 2 or self.total_answer_chars() < 120

    def _scenario_for(self, competency_id: str) -> str:
        if self._model:
            comp = next((c for c in self._model.competencies if c.id == competency_id), None)
            if comp:
                return f"{comp.name}深化"
            return "综合面试"
        role = role_by_id(self.state.job_id) if hasattr(self, "state") else role_by_id("product_manager")
        competency = next((item for item in role.competencies if item.id == competency_id), None)
        if competency:
            return f"{competency.name}深化"
        if competency_id == "project_delivery":
            return "项目推进深化"
        if competency_id == "impact_expression":
            return "项目结果表达深化"
        return "项目经历深化"

    def _opening_question_for(
        self,
        competency_id: str,
        strategy_id: str,
        company_card: CompanyIntelligenceCard | None = None,
    ) -> str:
        if self._model:
            return self._model.opening_question or f"你好，我们开始{self._model.job_title}模拟面试。请先讲一个能体现你核心能力的项目经历。"

        strategy_suffix = {
            "clarification_probe": "我会先把背景和角色问清楚。",
            "evidence_probe": "我会重点追问证据、细节和个人贡献。",
            "result_probe": "我会重点追问结果、指标和影响。",
            "reflection_probe": "我会重点追问复盘、取舍和改进。",
        }.get(strategy_id, "我会重点追问证据、细节和个人贡献。")

        if company_card:
            verify_note = "我会把公司了解作为加分项。" if company_card.verification_status != "unverified" else "公司资料目前待核验，我会重点看你的准备思路和岗位连接。"
            return f"你好，我们开始{self.state.job_name}模拟面试。请先说说你对{company_card.company_name}和{company_card.target_role}的理解。{verify_note}{strategy_suffix}"

        role = role_by_id(self.state.job_id)
        competency = next((item for item in role.competencies if item.id == competency_id), None)
        if competency:
            return f"你好，我们开始{self.state.job_name}模拟面试。请先讲一个能体现{competency.name}的经历，说明背景、你的动作和结果。{strategy_suffix}"
        return PRODUCT_MANAGER_OPENING

    def _next_capability_id(self) -> str:
        tracks = self._active_tracks()
        weights = self.state.competency_weights or self._default_competency_weights(self.state.job_id)
        counts = Counter(turn.capability_id for turn in self.state.turns)

        def priority(track: CapabilityTrack) -> tuple[float, float, int]:
            weight = max(1, weights.get(track.id, 1))
            desired = weight / max(1, sum(max(1, weights.get(item.id, 1)) for item in tracks))
            target_next_count = desired * (self.state.candidate_turn_count + 1)
            coverage_gap = 1 - self._track_coverage(track)
            return (target_next_count - counts[track.id], coverage_gap, -counts[track.id])

        return max(tracks, key=priority).id

    def _next_question_style_id(self) -> str:
        weights = self.state.question_style_weights or self._default_question_style_weights()
        usable_weights = {key: max(0, value) for key, value in weights.items() if value > 0}
        if not usable_weights:
            usable_weights = self._default_question_style_weights()
        counts = Counter(turn.question_style_id for turn in self.state.turns)
        total_weight = sum(usable_weights.values()) or 1

        def priority(style_id: str) -> tuple[float, int]:
            desired = usable_weights[style_id] / total_weight
            target_next_count = desired * (self.state.candidate_turn_count + 1)
            return (target_next_count - counts[style_id], -counts[style_id])

        return max(usable_weights, key=priority)

    def _covered_track_count(self) -> int:
        return sum(1 for track in self._active_tracks() if self._track_coverage(track) >= 0.5)

    def _track_coverage(self, track: CapabilityTrack) -> float:
        if not track.requirements:
            return 0.0
        covered = sum(1 for item in track.requirements if self._requirement_present(item.keywords))
        return covered / len(track.requirements)

    def _requirement_present(self, keywords: tuple[str, ...]) -> bool:
        answers = "\n".join(turn.answer for turn in self.state.turns)
        keyword_hit = any(keyword in answers for keyword in keywords)
        metric_hit = any(keyword in keywords for keyword in ("%", "数据", "指标", "转化")) and any(ch.isdigit() for ch in answers)
        return keyword_hit or metric_hit

    def _track_by_id(self, track_id: str) -> CapabilityTrack | None:
        return next((track for track in self._active_tracks() if track.id == track_id), None)

    def _track_name(self, track_id: str) -> str:
        track = self._track_by_id(track_id)
        return track.name if track else track_id

    def _question_style_name(self, style_id: str) -> str:
        return {
            "open": "开放提问",
            "evidence": "证据追问",
            "pressure": "压力追问",
            "relaxed": "轻松提问",
            "reflection": "复盘提问",
        }.get(style_id, style_id)

    def _interviewer_tone_prompt(self, fallback: str) -> str:
        tone = self.state.interviewer_tone or "encouraging"
        tone_prompt = {
            "encouraging": "语气鼓励、清晰，允许候选人逐步展开，但不要替他作答。",
            "formal": "语气正式、克制，像真实结构化面试，问题要准确专业。",
            "pressure": "语气更直接，重点挑战证据、逻辑和边界，但不得攻击候选人。",
            "relaxed": "语气轻松自然，先降低紧张感，再逐步追问关键证据。",
            "calm": "语气沉稳，关注结构、取舍和业务判断，不急不躁。",
        }.get(tone, fallback)
        return f"{tone_prompt} 基础声音档位：{fallback}"

    def _question_trace_reason(
        self,
        track: CapabilityTrack,
        style_id: str,
        missing_requirements: list[str],
    ) -> str:
        missing_text = "、".join(missing_requirements[:3]) if missing_requirements else "该能力证据已较完整"
        return (
            f"按当前能力权重优先采集「{track.name}」，"
            f"并按提问方式占比采用「{self._question_style_name(style_id)}」。"
            f"本轮主要补齐：{missing_text}。"
        )

    def _active_tracks(self) -> tuple[CapabilityTrack, ...]:
        if self._model:
            # 从动态模型构建能力轨道
            evidence_map: dict[str, tuple[DynamicEvidenceRequirement, ...]] = dict(self._model.evidence_requirements)
            tracks: list[CapabilityTrack] = []
            for comp in self._model.competencies:
                ev_reqs = evidence_map.get(comp.id, ())
                if not ev_reqs:
                    # 从 observable_signals 自动生成
                    ev_reqs = tuple(
                        DynamicEvidenceRequirement(
                            id=f"sig_{i}",
                            name=sig,
                            description=f"回答中需要体现：{sig}",
                            keywords=tuple(sig[:4]) if len(sig) >= 4 else (sig,),
                        )
                        for i, sig in enumerate(comp.observable_signals)
                    )
                tracks.append(CapabilityTrack(
                    id=comp.id,
                    name=comp.name,
                    description=comp.description,
                    requirements=tuple(
                        EvidenceRequirement(
                            id=req.id,
                            name=req.name,
                            description=req.description,
                            keywords=req.keywords,
                        )
                        for req in ev_reqs
                    ),
                ))
            return tuple(tracks) or CAPABILITY_TRACKS

        role = role_by_id(self.state.job_id)
        return tuple(
            CapabilityTrack(
                id=item.id,
                name=item.name,
                description=item.description,
                requirements=tuple(
                    self._requirement_from_signal(index, signal)
                    for index, signal in enumerate(item.observable_signals)
                ),
            )
            for item in role.competencies
        ) or CAPABILITY_TRACKS

    def _default_competency_weights(self, role_id: str) -> dict[str, int]:
        role = role_by_id(role_id)
        return {item.id: int(item.default_weight) for item in role.competencies}

    def _default_question_style_weights(self) -> dict[str, int]:
        return {
            "open": 30,
            "evidence": 30,
            "pressure": 15,
            "relaxed": 15,
            "reflection": 10,
        }

    def _requirement_from_signal(self, index: int, signal: str):
        from interview.models import EvidenceRequirement

        keywords = tuple(word for word in signal.replace("，", " ").replace("、", " ").split() if word)
        return EvidenceRequirement(f"signal_{index}", signal, f"回答中需要体现：{signal}", keywords or (signal[:2],))

    def _company_context_text(self) -> str:
        card = self.state.company_card
        if not card:
            return "未配置目标公司。"
        return "\n".join(
            [
                f"- 公司：{card.company_name}",
                f"- 岗位：{card.target_role}",
                f"- 核验状态：{card.verification_status}，可信度：{card.confidence}",
                f"- 摘要：{card.summary}",
                f"- 业务线：{'；'.join(card.business_lines) or '无'}",
                f"- 公司理解加分项：{'；'.join(card.role_relevant_points) or '无'}",
                f"- 来源：{'；'.join(card.source_notes) or '无'}",
            ]
        )
