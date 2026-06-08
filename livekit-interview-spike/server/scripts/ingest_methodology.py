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

from interview.followup.rag.embeddings import embedding_provider_from_env
from interview.followup.rag.ingest import ingest_sources, load_sources_from_jsonl
from interview.followup.rag.qdrant_store import qdrant_store_from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest interview methodology JSONL into Qdrant.")
    parser.add_argument("--file", required=True, help="Path to methodology JSONL file.")
    parser.add_argument("--chunk-size", type=int, default=int(os.getenv("RAG_CHUNK_SIZE", "900")))
    parser.add_argument("--chunk-overlap", type=int, default=int(os.getenv("RAG_CHUNK_OVERLAP", "120")))
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


async def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    args = parse_args()
    sources = load_sources_from_jsonl(args.file)
    if not sources:
        raise RuntimeError(f"No methodology sources found in {args.file}")

    embedding_provider = embedding_provider_from_env()
    vector_store = qdrant_store_from_env()
    report = await ingest_sources(
        sources=sources,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
    )
    print(
        f"Ingested {report.source_count} sources / {report.chunk_count} chunks "
        f"into Qdrant collection '{report.collection}'."
    )


if __name__ == "__main__":
    asyncio.run(main())
