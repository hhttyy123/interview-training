import json
import re
from typing import Any

from interview.configs import RUBRIC_DIMENSIONS
from interview.orchestrator import InterviewOrchestrator
from local_providers import ConversationMessage, DeepSeekStreamingTextProvider


SCORE_MIN = 0
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

        text = ""
        prompt = orchestrator.build_evaluation_prompt()
        async for chunk in llm_provider.stream_reply([ConversationMessage("user", prompt)], system_prompt="你只输出合法 JSON。"):
            text += chunk

        parsed = self._parse_json(text)
        if parsed:
            return self._normalize_report(parsed, orchestrator)
        return self._fallback_report(orchestrator, reason="LLM 评分 JSON 解析失败")

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
        report.setdefault("ability_model", self._ability_model_from_dimensions(report.get("dimensions", [])))
        report.setdefault("training_plan", self._default_training_plan())
        return report

    def _ability_model_from_dimensions(self, dimensions: Any) -> dict[str, int]:
        default = {item.id: SCORE_MIN for item in RUBRIC_DIMENSIONS}
        if not isinstance(dimensions, list):
            return default
        for item in dimensions:
            if not isinstance(item, dict):
                continue
            dimension_id = str(item.get("id", ""))
            score = item.get("score")
            if dimension_id in default and isinstance(score, int):
                default[dimension_id] = max(SCORE_MIN, min(SCORE_MAX, score))
        return default

    def _insufficient_sample_report(self, orchestrator: InterviewOrchestrator) -> dict[str, Any]:
        answer_text = "\n".join(turn.answer for turn in orchestrator.turns).strip()
        return {
            "report_quality": "insufficient_sample",
            "summary": "本轮回答样本太少，不能生成可信评分。当前只做初步诊断：需要先补充完整项目背景、个人动作和结果证据。",
            "turn_count": orchestrator.state.candidate_turn_count,
            "coverage_ratio": round(orchestrator.coverage_ratio(), 2),
            "ability_model": {item.id: SCORE_MIN for item in RUBRIC_DIMENSIONS},
            "dimensions": [
                {
                    "id": item.id,
                    "name": item.name,
                    "score": SCORE_MIN,
                    "level": "样本不足",
                    "reason": "候选人回答轮次或内容长度不足，不能进行稳定评分。",
                    "evidence": answer_text[:160] or "没有捕获到足够回答内容。",
                    "risk": "真实面试中，面试官会认为信息不足，无法判断能力强弱。",
                    "improvement": "先完成至少 3 个完整回答，覆盖背景、行动、结果和复盘，再生成正式评分。",
                }
                for item in RUBRIC_DIMENSIONS
            ],
            "evidence_gaps": [
                "项目背景和目标不完整",
                "个人关键动作不足",
                "结果证据不足",
                "复盘和改进不足",
            ],
            "main_weakness": "当前最大问题不是某项能力低，而是样本不足，无法支撑可信判断。",
            "training_plan": {
                "theme": "补全项目经历基础素材",
                "goal": "先把一个项目讲完整，再进入正式评分。",
                "duration_minutes": 10,
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

    def _fallback_report(self, orchestrator: InterviewOrchestrator, *, reason: str) -> dict[str, Any]:
        answer_text = "\n".join(turn.answer for turn in orchestrator.turns)
        has_number = any(ch.isdigit() for ch in answer_text)
        has_result = any(word in answer_text for word in ("结果", "提升", "降低", "用户", "数据", "反馈", "上线"))
        base_score = 6 if len(answer_text) >= 260 else 4
        evidence_score = min(8, base_score + 2) if has_number or has_result else base_score

        dimensions = []
        for item in RUBRIC_DIMENSIONS:
            score = evidence_score if item.id == "experience_evidence" else base_score
            dimensions.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "score": score,
                    "level": "初步判断",
                    "reason": f"{reason}，已使用规则兜底生成初步判断。",
                    "evidence": answer_text[:180] or "本轮没有捕获到有效候选人回答。",
                    "risk": "规则兜底不能替代正式评分，需要重新生成或补充回答。",
                    "improvement": item.normal_anchor,
                }
            )

        return {
            "report_quality": "fallback",
            "summary": "本轮已生成规则兜底报告，可信度低于正式评分。",
            "turn_count": orchestrator.state.candidate_turn_count,
            "coverage_ratio": round(orchestrator.coverage_ratio(), 2),
            "ability_model": {item["id"]: item["score"] for item in dimensions},
            "dimensions": dimensions,
            "evidence_gaps": self._evidence_gaps_from_snapshot(orchestrator.evidence_snapshot_text()),
            "main_weakness": "需要补充更具体的项目证据、个人贡献和结果表达。",
            "training_plan": self._default_training_plan(),
        }

    def _evidence_gaps_from_snapshot(self, snapshot: str) -> list[str]:
        return [line.replace("- ", "").replace(": 缺失", "") for line in snapshot.splitlines() if line.endswith("缺失")][:6]

    def _default_training_plan(self) -> dict[str, Any]:
        return {
            "theme": "项目经历证据补强",
            "goal": "把项目回答从经历描述升级为有证据的能力证明。",
            "duration_minutes": 15,
            "tasks": [
                {
                    "name": "结果证据补全",
                    "exercise": "重新讲一次刚才的项目，必须包含目标、个人动作、结果证据和复盘。",
                    "method": "先写 4 个关键词，再用 90 秒语音回答一遍。",
                    "success_criteria": "至少包含一个数据、用户反馈或前后对比。",
                }
            ],
            "next_interview_focus": "继续围绕项目结果和个人贡献追问。",
        }
