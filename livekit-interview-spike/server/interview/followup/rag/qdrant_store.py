from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from typing import Any

from interview.followup.rag.models import MethodologyChunk, RetrievalQuery, RetrievalResult


class QdrantVectorStore:
    def __init__(self, *, url: str, collection_name: str) -> None:
        self.url = url
        self.collection_name = collection_name
        self._client = None

    @property
    def client(self) -> Any:
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url)
        return self._client

    async def ensure_collection(self, *, vector_size: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    async def upsert_chunks(
        self,
        *,
        chunks: Sequence[MethodologyChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        from qdrant_client.models import PointStruct

        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=list(vector),
                payload=_chunk_payload(chunk),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(
        self,
        *,
        query_vector: Sequence[float],
        query: RetrievalQuery,
    ) -> list[RetrievalResult]:
        results = _search_points(
            client=self.client,
            collection_name=self.collection_name,
            query_vector=list(query_vector),
            query_filter=_build_filter(query),
            limit=query.limit,
        )
        return [
            RetrievalResult(
                chunk=_chunk_from_payload(point.payload or {}),
                score=float(point.score),
                payload=point.payload or {},
            )
            for point in results
        ]


def qdrant_store_from_env() -> QdrantVectorStore:
    return QdrantVectorStore(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection_name=os.getenv("QDRANT_COLLECTION", "interview_methodology"),
    )


def _search_points(
    *,
    client: Any,
    collection_name: str,
    query_vector: list[float],
    query_filter: Any,
    limit: int,
) -> list[Any]:
    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return list(response.points)
    return list(
        client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
    )


def _chunk_payload(chunk: MethodologyChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "title": chunk.title,
        "text": chunk.text,
        "ordinal": chunk.ordinal,
        "source_type": chunk.source_type,
        "source_url": chunk.source_url,
        "license_note": chunk.license_note,
        **chunk.metadata,
    }


def _chunk_from_payload(payload: dict[str, Any]) -> MethodologyChunk:
    reserved = {
        "chunk_id",
        "source_id",
        "title",
        "text",
        "ordinal",
        "source_type",
        "source_url",
        "license_note",
    }
    return MethodologyChunk(
        chunk_id=str(payload.get("chunk_id", "")),
        source_id=str(payload.get("source_id", "")),
        title=str(payload.get("title", "")),
        text=str(payload.get("text", "")),
        ordinal=int(payload.get("ordinal", 0)),
        source_type=str(payload.get("source_type", "methodology")),
        source_url=str(payload.get("source_url", "")),
        license_note=str(payload.get("license_note", "")),
        metadata={key: value for key, value in payload.items() if key not in reserved},
    )


def _build_filter(query: RetrievalQuery) -> Any:
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

    must: list[Any] = []
    if query.strategy_category:
        must.append(FieldCondition(key="strategy_categories", match=MatchValue(value=query.strategy_category)))
    if query.role_family:
        must.append(FieldCondition(key="role_families", match=MatchValue(value=query.role_family)))
    if query.competency_archetypes:
        must.append(
            FieldCondition(
                key="competency_archetypes",
                match=MatchAny(any=list(query.competency_archetypes)),
            )
        )
    if query.evidence_categories:
        must.append(
            FieldCondition(
                key="evidence_categories",
                match=MatchAny(any=list(query.evidence_categories)),
            )
        )
    if not must:
        return None
    return Filter(must=must)
