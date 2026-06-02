from collections import Counter

from interview.configs import (
    CAPABILITY_TRACKS,
    MODE_BEHAVIOR,
    PRODUCT_MANAGER_OPENING,
    RUBRIC_DIMENSIONS,
    STRATEGY_FOCUS,
)
from interview.models import CapabilityTrack, InterviewState, InterviewTurn


class InterviewOrchestrator:
    def __init__(self) -> None:
        self.state = InterviewState(last_question=PRODUCT_MANAGER_OPENING)

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
        mode_id: str = "standard",
        competency_id: str = "requirement_analysis",
        strategy_id: str = "evidence_probe",
    ) -> None:
        self.state = InterviewState(
            job_name="产品经理",
            scenario=self._scenario_for(competency_id),
            mode_id=mode_id,
            competency_id=competency_id,
            strategy_id=strategy_id,
            current_capability_id=competency_id if self._track_by_id(competency_id) else "requirement_analysis",
            last_question=self._opening_question_for(competency_id, strategy_id),
        )

    def record_candidate_answer(self, answer: str) -> None:
        self.state.turns.append(
            InterviewTurn(
                question=self.state.last_question,
                answer=answer.strip(),
                capability_id=self.state.current_capability_id,
            )
        )
        self.state.current_capability_id = self._next_capability_id()

    def record_assistant_question(self, question: str) -> None:
        self.state.last_question = question.strip()

    def closing_text(self) -> str:
        return "本轮面试已结束，报告已生成。"

    def coverage_ratio(self) -> float:
        total = sum(len(track.requirements) for track in CAPABILITY_TRACKS)
        if total == 0:
            return 0.0
        covered = sum(1 for track in CAPABILITY_TRACKS for requirement in track.requirements if self._requirement_present(requirement.keywords))
        return covered / total

    def build_followup_prompt(self) -> str:
        current_track = self._track_by_id(self.state.current_capability_id) or CAPABILITY_TRACKS[0]
        asked_turns = "\n".join(
            f"Q{i + 1}: {turn.question}\nA{i + 1}: {turn.answer}" for i, turn in enumerate(self.state.turns)
        )
        requirements = "\n".join(
            f"- {item.name}: {item.description}（当前状态：{'已出现' if self._requirement_present(item.keywords) else '待采集'}）"
            for item in current_track.requirements
        )
        all_tracks = "\n".join(f"- {track.name}: {track.description}" for track in CAPABILITY_TRACKS)

        last_answer = self.state.turns[-1].answer if self.state.turns else ""

        return f"""
你是一个面向应届生的公司岗位级 AI 面试训练教练，正在做结构化语音模拟面试。

当前面试：
- 岗位：{self.state.job_name}
- 场景：{self.state.scenario}
- 已完成候选人回答轮次：{self.state.candidate_turn_count}
- 最少轮次：{self.state.min_candidate_turns}
- 上限轮次：{self.state.max_candidate_turns}
- 模式：{MODE_BEHAVIOR.get(self.state.mode_id, MODE_BEHAVIOR["standard"])}
- 追问方式：{STRATEGY_FOCUS.get(self.state.strategy_id, STRATEGY_FOCUS["evidence_probe"])}

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
- 优先补齐当前能力中“待采集”的证据。
- 如果当前能力已较充分，就自然切到下一条能力轨道。
- 不要连续两轮纠缠同一个缺失点。
- 必须明显体现当前模式和追问方式，不能所有模式都问成同一种语气。
- 不要输出评分、分析、Markdown 或解释。
- 回复中文，控制在 60 个汉字以内，适合语音播报。
""".strip()

    def build_evaluation_prompt(self) -> str:
        transcript = "\n".join(
            f"面试官：{turn.question}\n候选人：{turn.answer}\n考察能力：{self._track_name(turn.capability_id)}"
            for turn in self.state.turns
        )
        rubric = "\n".join(
            f"- {item.id}/{item.name}: {item.description}；2分：{item.weak_anchor}；6分：{item.normal_anchor}；9-10分：{item.strong_anchor}"
            for item in RUBRIC_DIMENSIONS
        )
        evidence_snapshot = self.evidence_snapshot_text()

        return f"""
你是 AI 求职训练产品的结构化面试复盘教练。
请基于“对话原文 + 证据采集状态 + 行为锚定评分标准”生成报告。

重要要求：
- 如果证据不足，要明确说证据不足，不要写得像完整面试已经充分评价。
- 不要用模板化空话。
- 每个分数必须能对应候选人回答中的具体证据或明确缺失项。
- 训练计划要体系化、具体、可执行，但不要幻想不存在的经历。
- 分数范围是 1-10，1-3 是明显不足，4-6 是基本可用，7-8 是较好，9-10 是优秀。

评分维度：
{rubric}

证据采集状态：
{evidence_snapshot}

对话记录：
{transcript}

只输出 JSON，结构如下：
{{
  "report_quality": "full",
  "summary": "整体表现总结，必须包含最关键短板",
  "ability_model": {{
    "answer_structure": 2,
    "experience_evidence": 2,
    "job_understanding": 2,
    "project_delivery": 2,
    "expression_clarity": 2
  }},
  "dimensions": [
    {{
      "id": "answer_structure",
      "name": "回答结构",
      "score": 2,
      "level": "薄弱/基础/较好/优秀",
      "reason": "为什么这样打分",
      "evidence": "引用或概括候选人回答中的具体依据；如果没有就写缺失",
      "risk": "真实面试中可能被质疑的问题",
      "improvement": "提升到下一档需要补什么"
    }}
  ],
  "evidence_gaps": ["还缺哪些关键证据"],
  "main_weakness": "最影响面试表现的短板",
  "training_plan": {{
    "theme": "下一阶段训练主题",
    "goal": "训练目标",
    "duration_minutes": 15,
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
        for track in CAPABILITY_TRACKS:
            lines.append(f"{track.name}:")
            for requirement in track.requirements:
                status = "已出现" if self._requirement_present(requirement.keywords) else "缺失"
                lines.append(f"- {requirement.name}: {status}")
        return "\n".join(lines)

    def total_answer_chars(self) -> int:
        return sum(len(turn.answer.strip()) for turn in self.state.turns)

    def is_sample_insufficient(self) -> bool:
        return self.state.candidate_turn_count < 3 or self.total_answer_chars() < 180

    def _scenario_for(self, competency_id: str) -> str:
        if competency_id == "project_delivery":
            return "项目推进深化"
        if competency_id == "impact_expression":
            return "项目结果表达深化"
        return "项目经历深化"

    def _opening_question_for(self, competency_id: str, strategy_id: str) -> str:
        strategy_suffix = {
            "clarification_probe": "我会先把背景和角色问清楚。",
            "evidence_probe": "我会重点追问证据、细节和个人贡献。",
            "result_probe": "我会重点追问结果、指标和影响。",
            "reflection_probe": "我会重点追问复盘、取舍和改进。",
        }.get(strategy_id, "我会重点追问证据、细节和个人贡献。")

        if competency_id == "project_delivery":
            return f"你好，我们开始项目推进能力深挖。请先讲一个你负责推动落地的项目，说明你的角色和关键动作。{strategy_suffix}"
        if competency_id == "impact_expression":
            return f"你好，我们开始结果表达能力深挖。请先讲一个有明确结果的项目，说明目标、结果和你的贡献。{strategy_suffix}"
        return f"你好，我们开始需求分析能力深挖。请先讲一个你判断或定义需求的项目，说明需求来源和用户问题。{strategy_suffix}"

    def _next_capability_id(self) -> str:
        counts = Counter(turn.capability_id for turn in self.state.turns)
        primary_track = self._track_by_id(self.state.competency_id) or CAPABILITY_TRACKS[0]
        if counts[primary_track.id] < 3:
            return primary_track.id
        for track in CAPABILITY_TRACKS:
            if track.id != primary_track.id and counts[track.id] < 1:
                return track.id
        weakest = min(CAPABILITY_TRACKS, key=lambda track: self._track_coverage(track))
        return weakest.id

    def _covered_track_count(self) -> int:
        return sum(1 for track in CAPABILITY_TRACKS if self._track_coverage(track) >= 0.5)

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
        return next((track for track in CAPABILITY_TRACKS if track.id == track_id), None)

    def _track_name(self, track_id: str) -> str:
        track = self._track_by_id(track_id)
        return track.name if track else track_id
