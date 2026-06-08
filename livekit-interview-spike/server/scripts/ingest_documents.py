from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interview.followup.rag.document_loader import load_methodology_documents
from interview.followup.rag.embeddings import embedding_provider_from_env
from interview.followup.rag.ingest import ingest_sources
from interview.followup.rag.qdrant_store import qdrant_store_from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest .txt/.md/.pdf/.docx methodology documents into Qdrant.")
    parser.add_argument("--path", required=True, help="Document file or directory path.")
    parser.add_argument("--source-type", default="internal_note")
    parser.add_argument("--license-note", default="用户提供或项目内部整理资料")
    parser.add_argument("--strategy-categories", default="")
    parser.add_argument("--role-families", default="general")
    parser.add_argument("--competency-archetypes", default="")
    parser.add_argument("--evidence-categories", default="")
    parser.add_argument("--chunk-size", type=int, default=int(os.getenv("RAG_CHUNK_SIZE", "900")))
    parser.add_argument("--chunk-overlap", type=int, default=int(os.getenv("RAG_CHUNK_OVERLAP", "120")))
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


async def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    args = parse_args()
    sources = load_methodology_documents(
        path=args.path,
        source_type=args.source_type,
        license_note=args.license_note,
        metadata={
            "strategy_categories": _csv(args.strategy_categories),
            "role_families": _csv(args.role_families),
            "competency_archetypes": _csv(args.competency_archetypes),
            "evidence_categories": _csv(args.evidence_categories),
        },
    )
    if not sources:
        raise RuntimeError(f"No supported documents with extractable text found under {args.path}")

    report = await ingest_sources(
        sources=sources,
        embedding_provider=embedding_provider_from_env(),
        vector_store=qdrant_store_from_env(),
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
    )
    print(
        f"Ingested {report.source_count} documents / {report.chunk_count} chunks "
        f"into Qdrant collection '{report.collection}'."
    )


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    asyncio.run(main())
