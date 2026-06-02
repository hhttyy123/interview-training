from interview.configs import (
    COMPETENCY_FOCUS,
    MODE_BEHAVIOR,
    PRODUCT_MANAGER_COMPETENCIES,
    PRODUCT_MANAGER_OPENING,
    RUBRIC_DIMENSIONS,
    STRATEGY_FOCUS,
)
from interview.models import InterviewState, InterviewTurn


class InterviewOrchestrator:
    def __init__(self) -> None:
        self.state = InterviewState(last_question=PRODUCT_MANAGER_OPENING)

    @property
    def opening_question(self) -> str:
        return PRODUCT_MANAGER_OPENING

    @property
    def should_finish(self) -> bool:
        return self.state.should_finish

    @property
    def turns(self) -> list[InterviewTurn]:
        return self.state.turns

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
            job_name="产品经理" if job_id == "product_manager" else "产品经理",
            scenario=self._scenario_for(competency_id),
            mode_id=mode_id,
            competency_id=competency_id,
            strategy_id=strategy_id,
            last_question=PRODUCT_MANAGER_OPENING,
        )

    def record_candidate_answer(self, answer: str) -> None:
        self.state.turns.append(InterviewTurn(question=self.state.last_question, answer=answer.strip()))

    def record_assistant_question(self, question: str) -> None:
        self.state.last_question = question.strip()

    def closing_text(self) -> str:
        return "这轮项目经历深挖先到这里。我会根据刚才的回答生成一份简短评分和下一轮训练建议。"

    def build_followup_prompt(self) -> str:
        asked_turns = "\n".join(
            f"Q{i + 1}: {turn.question}\nA{i + 1}: {turn.answer}" for i, turn in enumerate(self.state.turns)
        )
        competencies = "\n".join(f"- {item}" for item in PRODUCT_MANAGER_COMPETENCIES)
        dimensions = "\n".join(f"- {item.name}: {item.description}" for item in RUBRIC_DIMENSIONS)

        return f"""
你是一个面向应届生的公司岗位级 AI 面试训练教练。

当前面试：
- 岗位：{self.state.job_name}
- 场景：{self.state.scenario}
- 当前进度：第 {self.state.candidate_turn_count + 1} 个候选人回答后继续追问
- 模式：{MODE_BEHAVIOR.get(self.state.mode_id, MODE_BEHAVIOR["standard"])}
- 能力重点：{COMPETENCY_FOCUS.get(self.state.competency_id, COMPETENCY_FOCUS["requirement_analysis"])}
- 追问方式：{STRATEGY_FOCUS.get(self.state.strategy_id, STRATEGY_FOCUS["evidence_probe"])}

你要像真实结构化面试官一样追问，不要像聊天助手。

本轮重点观察能力：
{competencies}

面后会评分的维度：
{dimensions}

已经发生的对话：
{asked_turns}

追问原则：
- 每次只问一个问题。
- 必须基于候选人上一轮回答继续追问。
- 优先补齐：项目背景、用户问题、候选人个人动作、取舍依据、结果证据、复盘反思。
- 如果某个角度已经比较清楚，就换到下一个更有价值的角度。
- 不要连续两轮纠缠同一个缺失点。
- 不要输出评分、分析、markdown 或解释。
- 回复中文，尽量控制在 60 个汉字以内，适合语音播报。
""".strip()

    def _scenario_for(self, competency_id: str) -> str:
        if competency_id == "project_delivery":
            return "项目推进深挖"
        if competency_id == "impact_expression":
            return "项目结果表达深挖"
        return "项目经历深挖"

    def build_evaluation_prompt(self) -> str:
        transcript = "\n".join(
            f"面试官：{turn.question}\n候选人：{turn.answer}" for turn in self.state.turns
        )
        rubric = "\n".join(
            f"- {item.id} / {item.name}: {item.description}；弱表现：{item.weak_anchor}；强表现：{item.strong_anchor}"
            for item in RUBRIC_DIMENSIONS
        )

        return f"""
你是 AI 求职训练产品的面试复盘教练。
请根据下面这轮产品经理项目经历深挖，生成结构化评分和下一轮训练方案。

评分维度：
{rubric}

对话记录：
{transcript}

输出要求：
- 只输出 JSON，不要 markdown。
- score 必须是 1 到 5 的整数。
- evidence 必须引用或概括候选人刚才回答中的具体依据，不能凭空编造。
- feedback 要具体、可执行。
- training_plan 要短，适合用户下一轮 10 分钟训练。

JSON 结构：
{{
  "summary": "本轮整体表现一句话总结",
  "dimensions": [
    {{
      "id": "structure",
      "name": "回答结构",
      "score": 3,
      "reason": "为什么这样打分",
      "evidence": "来自候选人回答的依据",
      "improvement": "下一步如何改"
    }}
  ],
  "main_weakness": "当前最影响面试表现的短板",
  "training_plan": {{
    "theme": "下一轮训练主题",
    "goal": "训练目标",
    "exercise": "建议练习题",
    "method": "练习方法",
    "duration_minutes": 10
  }}
}}
""".strip()
