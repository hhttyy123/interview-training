import json
import re
from typing import Any

from interview.configs import RUBRIC_DIMENSIONS
from interview.orchestrator import InterviewOrchestrator
from local_providers import ConversationMessage, DeepSeekStreamingTextProvider


class InterviewEvaluator:
    async def evaluate(
        self,
        *,
        orchestrator: InterviewOrchestrator,
        llm_provider: DeepSeekStreamingTextProvider,
    ) -> dict[str, Any]:
        text = ""
        prompt = orchestrator.build_evaluation_prompt()
        async for chunk in llm_provider.stream_reply([ConversationMessage("user", prompt)], system_prompt="你只输出合法 JSON。"):
            text += chunk

        parsed = self._parse_json(text)
        if parsed:
            return parsed
        return self._fallback_report(orchestrator)

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
            if isinstance(payload, dict) and isinstance(payload.get("dimensions"), list):
                return payload
        return None

    def _fallback_report(self, orchestrator: InterviewOrchestrator) -> dict[str, Any]:
        answer_text = "\n".join(turn.answer for turn in orchestrator.turns)
        has_number = any(ch.isdigit() for ch in answer_text)
        has_result = any(word in answer_text for word in ("结果", "提升", "降低", "用户", "数据", "反馈", "上线"))
        base_score = 3 if len(answer_text) >= 80 else 2
        evidence_score = 4 if has_number or has_result else base_score

        dimensions = []
        for item in RUBRIC_DIMENSIONS:
            score = evidence_score if item.id == "evidence" else base_score
            dimensions.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "score": score,
                    "reason": "模型评分解析失败，已使用规则兜底生成初步判断。",
                    "evidence": answer_text[:120] or "本轮没有捕获到有效候选人回答。",
                    "improvement": item.weak_anchor,
                }
            )

        return {
            "summary": "本轮已完成基础复盘，但 LLM 评分 JSON 解析失败，以下为规则兜底结果。",
            "dimensions": dimensions,
            "main_weakness": "需要补充更具体的项目证据和结果表达。",
            "training_plan": {
                "theme": "项目经历证据补强",
                "goal": "把项目回答从经历描述升级为有证据的能力证明。",
                "exercise": "重新讲一次刚才的项目，必须包含目标、个人动作、结果证据和复盘。",
                "method": "先写 4 个关键词，再用 90 秒语音回答一遍。",
                "duration_minutes": 10,
            },
        }
