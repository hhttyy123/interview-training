from __future__ import annotations

from typing import Protocol, Sequence

from interview.followup.rag.models import MethodologyChunk, RetrievalQuery, RetrievalResult


class VectorStore(Protocol):
    collection_name: str

    async def ensure_collection(self, *, vector_size: int) -> None:
        ...

    async def upsert_chunks(
        self,
        *,
        chunks: Sequence[MethodologyChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        ...

    async def search(
        self,
        *,
        query_vector: Sequence[float],
        query: RetrievalQuery,
    ) -> list[RetrievalResult]:
        ...
