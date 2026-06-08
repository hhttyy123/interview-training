from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interview.followup.rag.embeddings import embedding_provider_from_env
from interview.followup.rag.models import RetrievalQuery
from interview.followup.rag.qdrant_store import qdrant_store_from_env
from interview.followup.rag.retriever import MethodologyRetriever


@dataclass(frozen=True)
class EvalCase:
    query_id: str
    query: str
    expected_source_ids: tuple[str, ...]
    strategy_category: str = ""
    question_style_id: str = ""
    interview_style_id: str = ""
    role_family: str = ""
    competency_archetypes: tuple[str, ...] = ()
    evidence_categories: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate methodology RAG retrieval quality.")
    parser.add_argument("--file", default="data/methodology.eval.jsonl", help="Evaluation JSONL file.")
    parser.add_argument("--limit", type=int, default=int(os.getenv("RAG_RETRIEVAL_LIMIT", "6")))
    return parser.parse_args()


async def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    args = parse_args()
    cases = load_eval_cases(args.file)
    if not cases:
        raise RuntimeError(f"No evaluation cases found in {args.file}")

    retriever = MethodologyRetriever(
        embedding_provider=embedding_provider_from_env(),
        vector_store=qdrant_store_from_env(),
    )

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_rank_sum = 0.0

    for case in cases:
        results = await retriever.retrieve(
            RetrievalQuery(
                query_text=case.query,
                limit=args.limit,
                strategy_category=case.strategy_category,
                question_style_id=case.question_style_id,
                interview_style_id=case.interview_style_id,
                role_family=case.role_family,
                competency_archetypes=case.competency_archetypes,
                evidence_categories=case.evidence_categories,
            )
        )
        retrieved = [result.chunk.source_id for result in results]
        rank = first_hit_rank(retrieved, case.expected_source_ids)
        if rank == 1:
            hits_at_1 += 1
        if rank and rank <= 3:
            hits_at_3 += 1
        if rank and rank <= 5:
            hits_at_5 += 1
        if rank:
            reciprocal_rank_sum += 1 / rank

        print(f"\n{case.query_id}")
        print(f"expected: {', '.join(case.expected_source_ids)}")
        print(f"rank: {rank or 'miss'}")
        for index, result in enumerate(results, start=1):
            print(f"{index}. {result.chunk.source_id} score={result.score:.4f} title={result.chunk.title}")

    total = len(cases)
    print("\nSummary")
    print(f"cases: {total}")
    print(f"hit@1: {hits_at_1 / total:.3f}")
    print(f"hit@3: {hits_at_3 / total:.3f}")
    print(f"hit@5: {hits_at_5 / total:.3f}")
    print(f"mrr: {reciprocal_rank_sum / total:.3f}")


def load_eval_cases(path: str | Path) -> list[EvalCase]:
    eval_path = Path(path)
    cases: list[EvalCase] = []
    with eval_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            cases.append(
                EvalCase(
                    query_id=str(payload.get("query_id", f"case-{line_number}")),
                    query=str(payload["query"]),
                    expected_source_ids=tuple(str(item) for item in payload["expected_source_ids"]),
                    strategy_category=str(payload.get("strategy_category", "")),
                    question_style_id=str(payload.get("question_style_id", "")),
                    interview_style_id=str(payload.get("interview_style_id", "")),
                    role_family=str(payload.get("role_family", "")),
                    competency_archetypes=tuple(str(item) for item in payload.get("competency_archetypes", [])),
                    evidence_categories=tuple(str(item) for item in payload.get("evidence_categories", [])),
                )
            )
    return cases


def first_hit_rank(retrieved: list[str], expected: tuple[str, ...]) -> int | None:
    expected_set = set(expected)
    for index, source_id in enumerate(retrieved, start=1):
        if source_id in expected_set:
            return index
    return None


if __name__ == "__main__":
    asyncio.run(main())
