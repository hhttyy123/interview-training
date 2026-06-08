from __future__ import annotations

from typing import Protocol

from interview.followup.rag.embeddings import EmbeddingProvider
from interview.followup.rag.models import RetrievalQuery, RetrievalResult
from interview.followup.rag.vector_store import VectorStore


class Reranker(Protocol):
    async def rerank(self, *, query: RetrievalQuery, results: list[RetrievalResult]) -> list[RetrievalResult]:
        ...


class NoopReranker:
    async def rerank(self, *, query: RetrievalQuery, results: list[RetrievalResult]) -> list[RetrievalResult]:
        return results


class MethodologyRetriever:
    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        reranker: Reranker | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.reranker = reranker or NoopReranker()

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        [query_vector] = await self.embedding_provider.embed_texts([build_retrieval_query_text(query)])
        results = await self.vector_store.search(query_vector=query_vector, query=query)
        return await self.reranker.rerank(query=query, results=results)


def build_retrieval_query_text(query: RetrievalQuery) -> str:
    parts = [
        query.query_text,
        f"strategy_category={query.strategy_category}" if query.strategy_category else "",
        f"question_style={query.question_style_id}" if query.question_style_id else "",
        f"interview_style={query.interview_style_id}" if query.interview_style_id else "",
        f"role_family={query.role_family}" if query.role_family else "",
        f"competency={','.join(query.competency_archetypes)}" if query.competency_archetypes else "",
        f"evidence={','.join(query.evidence_categories)}" if query.evidence_categories else "",
    ]
    return "\n".join(part for part in parts if part)
