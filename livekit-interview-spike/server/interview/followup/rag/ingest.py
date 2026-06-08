from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

from interview.followup.rag.chunker import chunk_methodology_source
from interview.followup.rag.embeddings import EmbeddingProvider
from interview.followup.rag.models import IngestionReport, MethodologySource
from interview.followup.rag.vector_store import VectorStore


async def ingest_sources(
    *,
    sources: Sequence[MethodologySource],
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStore,
    chunk_size: int = 900,
    chunk_overlap: int = 120,
    batch_size: int = 32,
) -> IngestionReport:
    chunks = [
        chunk
        for source in sources
        for chunk in chunk_methodology_source(
            source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    ]
    await vector_store.ensure_collection(vector_size=embedding_provider.dimension)

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = await embedding_provider.embed_texts([chunk.text for chunk in batch])
        await vector_store.upsert_chunks(chunks=batch, vectors=vectors)

    return IngestionReport(
        source_count=len(sources),
        chunk_count=len(chunks),
        collection=vector_store.collection_name,
    )


def load_sources_from_jsonl(path: str | Path) -> list[MethodologySource]:
    source_path = Path(path)
    return [source for source in _iter_jsonl_sources(source_path)]


def _iter_jsonl_sources(path: Path) -> Iterable[MethodologySource]:
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            try:
                yield MethodologySource(
                    source_id=str(payload["source_id"]),
                    title=str(payload["title"]),
                    content=str(payload["content"]),
                    source_type=str(payload.get("source_type", "methodology")),
                    source_url=str(payload.get("source_url", "")),
                    license_note=str(payload.get("license_note", "")),
                    metadata=dict(payload.get("metadata", {})),
                )
            except KeyError as exc:
                raise ValueError(f"Missing required field {exc} in {path}:{line_number}") from exc
