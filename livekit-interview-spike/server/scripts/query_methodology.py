from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interview.followup.rag.embeddings import embedding_provider_from_env
from interview.followup.rag.models import RetrievalQuery
from interview.followup.rag.qdrant_store import qdrant_store_from_env
from interview.followup.rag.retriever import MethodologyRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query the interview methodology RAG collection.")
    parser.add_argument("query", help="Search query.")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--strategy-category", default="")
    parser.add_argument("--role-family", default="")
    parser.add_argument("--competency-archetypes", default="")
    parser.add_argument("--evidence-categories", default="")
    parser.add_argument("--preview-chars", type=int, default=500)
    return parser.parse_args()


async def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    args = parse_args()
    retriever = MethodologyRetriever(
        embedding_provider=embedding_provider_from_env(),
        vector_store=qdrant_store_from_env(),
    )
    results = await retriever.retrieve(
        RetrievalQuery(
            query_text=args.query,
            limit=args.limit,
            strategy_category=args.strategy_category,
            role_family=args.role_family,
            competency_archetypes=tuple(_csv(args.competency_archetypes)),
            evidence_categories=tuple(_csv(args.evidence_categories)),
        )
    )
    for index, item in enumerate(results, start=1):
        preview = item.chunk.text[: args.preview_chars].replace("\n", " ")
        print(
            f"{index}. score={item.score:.4f} "
            f"ordinal={item.chunk.ordinal} title={item.chunk.title}\n{preview}\n"
        )


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    asyncio.run(main())
