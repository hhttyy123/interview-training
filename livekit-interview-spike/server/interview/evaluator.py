import json
import re
from typing import Any

from interview.configs import RUBRIC_DIMENSIONS
from interview.orchestrator import InterviewOrchestrator
from local_providers import ConversationMessage, DeepSeekStreamingTextProvider


SCORE_MIN = 1
SCORE_MAX = 10


class InterviewEvaluator:
    async def evaluate(
        self,
        *,
        orchestrator: InterviewOrchestrator,
        llm_provider: DeepSeekStreamingTextProvider,
    ) -> dict[str, Any]:
        if orchestrator.is_sample_insufficient():
            return self._insufficient_sample_report(orchestrator)

        prompt = orchestrator.build_evaluation_prompt()
        try:
            text = await llm_provider.complete_reply(
                [ConversationMessage("user", prompt)],
                system_prompt="你只输出合法 JSON。",
                temperature=0.0,
            )
        except Exception as error:
            return self._unavailable_report(orchestrator, reason=f"评分模型调用失败：{error}")

        parsed = self._parse_json(text)
        if parsed:
            return self._normalize_report(parsed, orchestrator)
        return self._unavailable_report(orchestrator, reason="评分模型返回格式异常，无法生成可信报告。")

    def _parse_json(self, raw: str) -> dict[str, Any] | None:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        candidates = [cleaned]
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            candidates.append(match.group(0))

        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return None

    def _normalize_report(self, report: dict[str, Any], orchestrator: InterviewOrchestrator) -> dict[str, Any]:
        report.setdefault("report_quality", "full")
        report.setdefault("evidence_snapshot", orchestrator.evidence_snapshot_text())
        report.setdefault("turn_count", orchestrator.state.candidate_turn_count)
        report.setdefault("coverage_ratio", round(orchestrator.coverage_ratio(), 2))
        self._normalize_dimensions_to_rubric(report, orchestrator)
        self._normalize_dimension_tone(report)
        report["ability_model"] = self._ability_model_from_dimensions(report.get("dimensions", []), orchestrator)
        return report

    def _rubric_dimensions(self, orchestrator: InterviewOrchestrator) -> Any:
        if orchestrator.has_dynamic_model and orchestrator._model:
            return orchestrator._model.rubric_dimensions
        return RUBRIC_DIMENSIONS

    def _normalize_dimensions_to_rubric(self, report: dict[str, Any], orchestrator: InterviewOrchestrator) -> None:
        dimensions = report.get("dimensions")
        if not isinstance(dimensions, list):
            return
        rubric_by_id = {item.id: item for item in self._rubric_dimensions(orchestrator)}
        for item in dimensions:
            if not isinstance(item, dict):
                continue
            dimension_id = str(item.get("id", "")).strip()
            rubric = rubric_by_id.get(dimension_id)
            if not rubric:
                continue
            item["id"] = rubric.id
            item["name"] = rubric.name
            score = item.get("score")
            if isinstance(score, int):
                item["score"] = max(SCORE_MIN, min(SCORE_MAX, score))

    def _normalize_dimension_tone(self, report: dict[str, Any]) -> None:
        dimensions = report.get("dimensions")
        if not isinstance(dimensions, list):
            return
        for item in dimensions:
            if not isinstance(item, dict):
                continue
            score = item.get("score")
            if isinstance(score, int):
                if score <= 2:
                    item["level"] = item.get("level") or "证据严重不足"
                elif score <= 4:
                    item["level"] = item.get("level") or "待补强"
                elif score <= 6:
                    item["level"] = item.get("level") or "基础可用"
            reason = str(item.get("reason", "")).strip()
            improvement = str(item.get("improvement", "")).strip()
            if reason and "已看到" not in reason and "优势" not in reason and "有效" not in reason:
                item["reason"] = f"当前判断：{reason}"
            if improvement and not improvement.startswith("下一步"):
                item["improvement"] = f"下一步可以这样补强：{improvement}"

    def _ability_model_from_dimensions(self, dimensions: Any, orchestrator: InterviewOrchestrator) -> dict[str, int]:
        default: dict[str, int] = {}
        if not isinstance(dimensions, list):
            return default
        # 获取有效维度 ID：优先动态模型，否则 RUBRIC_DIMENSIONS
        valid_ids = {d.id for d in self._rubric_dimensions(orchestrator)}
        for item in dimensions:
            if not isinstance(item, dict):
                continue
            dimension_id = str(item.get("id", ""))
            score = item.get("score")
            if dimension_id in valid_ids and isinstance(score, int):
                default[dimension_id] = max(SCORE_MIN, min(SCORE_MAX, score))
        return default

    def _insufficient_sample_report(self, orchestrator: InterviewOrchestrator) -> dict[str, Any]:
        answer_text = "\n".join(turn.answer for turn in orchestrator.turns).strip()
        # 使用动态评分维度或默认 RUBRIC_DIMENSIONS
        if orchestrator.has_dynamic_model and orchestrator._model:
            rubric_dims = orchestrator._model.rubric_dimensions
        else:
            rubric_dims = RUBRIC_DIMENSIONS
        return {
            "report_quality": "insufficient_sample",
            "summary": "本轮回答样本还不够完整，因此暂不做高低分判断。当前先给训练诊断：优先补充项目背景、个人动作和结果证据，下一轮再生成正式评分。",
            "turn_count": orchestrator.state.candidate_turn_count,
            "coverage_ratio": round(orchestrator.coverage_ratio(), 2),
            "ability_model": {},
            "dimensions": [
                {
                    "id": item.id,
                    "name": item.name,
                    "score": None,
                    "level": "暂不评分",
                    "reason": "当前只看到少量回答，暂不能稳定判断该维度强弱。",
                    "evidence": answer_text[:160] or "没有捕获到足够回答内容。",
                    "risk": "如果正式面试中也缺少这些信息，面试官会继续追问，而不是直接确认能力水平。",
                    "improvement": "下一步先完成至少 3 个完整回答，覆盖背景、行动、结果和复盘，再生成正式评分。",
                }
                for item in rubric_dims
            ],
            "evidence_gaps": [
                "项目背景和目标不完整",
                "个人关键动作不足",
                "结果证据不足",
                "复盘和改进不足",
            ],
            "company_fit_bonus": self._default_company_fit(orchestrator, insufficient=True),
            "role_fit": self._default_role_fit(orchestrator, insufficient=True),
            "main_weakness": "当前不是能力被判低，而是有效样本不足；先把一个项目讲完整。",
            "training_plan": {
                "theme": "补全项目经历基础素材",
                "goal": "先把一个项目讲完整，再进入正式评分。",
                "duration_minutes": 10,
                "seven_day_plan": [
                    "整理 1 个最完整项目，补齐背景、目标、个人动作、结果、复盘。",
                    "每天用 90 秒口头讲一次，并录音检查是否出现个人贡献和结果证据。",
                ],
                "fourteen_day_plan": [
                    "准备 2-3 个不同能力方向的项目素材，分别覆盖公司理解、岗位能力和协作推进。",
                    "每个项目至少补充 1 个数据、用户反馈或前后对比证据。",
                ],
                "thirty_day_plan": [
                    "形成稳定的面试素材库，并按不同岗位能力维度做专项模拟。",
                    "每周完成 2 次完整模拟面试，根据报告修正表达结构和证据链。",
                ],
                "tasks": [
                    {
                        "name": "项目五段式整理",
                        "exercise": "用背景、目标、个人动作、结果、复盘五段重新整理刚才的项目。",
                        "method": "每段先写 1 句关键词，再用 90 秒口头讲一遍。",
                        "success_criteria": "回答里必须出现个人负责内容、一个关键动作、一个结果证据。",
                    }
                ],
                "next_interview_focus": "下一轮先继续项目经历深化，不直接做压力追问。",
            },
        }

    def _unavailable_report(self, orchestrator: InterviewOrchestrator, *, reason: str) -> dict[str, Any]:
        return {
            "report_quality": "evaluation_unavailable",
            "summary": reason,
            "turn_count": orchestrator.state.candidate_turn_count,
            "coverage_ratio": round(orchestrator.coverage_ratio(), 2),
            "ability_model": {},
            "dimensions": [],
            "evidence_gaps": [],
            "company_fit_bonus": {"score": None, "reason": reason, "verification_note": "", "talking_points": []},
            "role_fit": {"score": None, "reason": reason, "focus_dimensions": [], "risk": ""},
            "main_weakness": "评分模型不可用，本轮不生成训练判断，避免输出规则伪报告。",
            "training_plan": {"theme": "等待重新生成正式报告", "goal": reason, "tasks": []},
        }

    def _evidence_gaps_from_snapshot(self, snapshot: str) -> list[str]:
        return [line.replace("- ", "").replace(": 缺失", "") for line in snapshot.splitlines() if line.endswith("缺失")][:6]

    def _default_company_fit(self, orchestrator: InterviewOrchestrator, *, insufficient: bool = False) -> dict[str, Any]:
        card = orchestrator.state.company_card
        if not card:
            return {
                "score": None,
                "reason": "本轮未配置目标公司，无法评估公司理解。",
                "verification_note": "未配置公司资料。",
                "talking_points": [],
            }
        if insufficient:
            return {
                "score": None,
                "reason": "回答样本不足，不能判断候选人对公司的理解是否可信。",
                "verification_note": f"公司资料状态：{card.verification_status}。",
                "talking_points": list(card.interview_talking_points),
            }
        return {
            "score": 5 if card.verification_status != "unverified" else 3,
            "reason": "评分模型未返回公司理解字段，当前仅保留资料状态，不作为正式表现判断。",
            "verification_note": f"公司资料状态：{card.verification_status}，可信度：{card.confidence}。",
            "talking_points": list(card.interview_talking_points),
        }

    def _default_role_fit(self, orchestrator: InterviewOrchestrator, *, insufficient: bool = False) -> dict[str, Any]:
        active_tracks = orchestrator.evidence_snapshot_text().splitlines()
        return {
            "score": None if insufficient else 5,
            "reason": "样本不足，暂不能判断岗位匹配。" if insufficient else "评分模型未返回岗位匹配字段，当前不作为正式岗位匹配判断。",
            "focus_dimensions": [line.replace(":", "") for line in active_tracks if line.endswith(":")][:6],
            "risk": "如果回答不能连接岗位能力模型，真实面试中会显得动机和经历不够匹配。",
        }
