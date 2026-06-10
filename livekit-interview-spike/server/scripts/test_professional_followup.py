from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interview.followup.professional_planner import build_professional_followup
from interview.models import CapabilityTrack, EvidenceRequirement, InterviewTurn
from local_providers import DeepSeekStreamingTextProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the professional follow-up planner without LiveKit.")
    parser.add_argument("--role", default="通用岗位")
    parser.add_argument("--competency-id", default="execution_delivery")
    parser.add_argument("--competency-name", default="执行交付")
    parser.add_argument("--competency-description", default="推动任务落地并交付可验证结果")
    parser.add_argument("--question", default="请讲一个你推动项目落地的经历。")
    parser.add_argument("--answer", required=True)
    parser.add_argument("--question-style", default="evidence")
    parser.add_argument("--interview-style", default="standard")
    parser.add_argument("--missing-evidence", default="个人行动,结果指标")
    parser.add_argument("--rag-limit", type=int, default=4)
    parser.add_argument("--show-prompt", action="store_true")
    return parser.parse_args()


async def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    args = parse_args()
    track = CapabilityTrack(
        id=args.competency_id,
        name=args.competency_name,
        description=args.competency_description,
        requirements=tuple(
            EvidenceRequirement(
                id=f"req_{index}",
                name=item,
                description=f"回答中需要体现：{item}",
                keywords=(item[:2],),
            )
            for index, item in enumerate(_csv(args.missing_evidence))
        ),
    )
    result = await build_professional_followup(
        role_name=args.role,
        current_track=track,
        question_style_id=args.question_style,
        interview_style_id=args.interview_style,
        turns=[
            InterviewTurn(
                question=args.question,
                answer=args.answer,
                capability_id=args.competency_id,
                question_style_id=args.question_style,
            )
        ],
        missing_evidence=tuple(_csv(args.missing_evidence)),
        provider=DeepSeekStreamingTextProvider(),
        rag_limit=args.rag_limit,
    )
    print("Planner")
    print(f"mode: {result.event_payload.get('plannerMode')}")
    print(f"timings: {result.event_payload.get('plannerTimings')}")
    print(f"gap: {result.gap.gap_types} confidence={result.gap.confidence}")
    print(f"gap_summary: {result.gap.answer_quality_summary}")
    print(f"target: {result.gap.best_next_probe_target}")
    print(f"strategy: {result.strategy_selection.card.strategy_id} score={result.strategy_selection.score:.2f}")
    print(f"selected_because: {result.strategy_selection.selected_because}")
    print()
    print("RAG")
    print(f"used: {bool(result.rag_results)}")
    print(f"query: {result.event_payload.get('ragQuery')}")
    for index, item in enumerate(result.rag_results, start=1):
        print(f"{index}. score={item.score:.4f} title={item.chunk.title} ordinal={item.chunk.ordinal}")
        print(item.chunk.text[:260].replace("\n", " "))
    if args.show_prompt:
        print()
        print("Prompt")
        print(result.prompt)


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    asyncio.run(main())
