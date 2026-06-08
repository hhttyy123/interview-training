from __future__ import annotations

import hashlib
import os
from typing import Protocol, Sequence

import httpx


class EmbeddingProvider(Protocol):
    dimension: int

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        dimension: int = 1536,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required for openai-compatible embeddings")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.dimension = dimension
        self.timeout_seconds = timeout_seconds

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": list(texts)},
            )
            response.raise_for_status()
            payload = response.json()
        vectors = [item["embedding"] for item in sorted(payload["data"], key=lambda item: item["index"])]
        if vectors and len(vectors[0]) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vectors[0])}"
            )
        return vectors


class LocalHashEmbeddingProvider:
    """Deterministic offline fallback for local smoke checks, not production retrieval quality."""

    def __init__(self, *, dimension: int = 384) -> None:
        self.dimension = dimension

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        values: list[float] = []
        seed = text.encode("utf-8")
        counter = 0
        while len(values) < self.dimension:
            digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            values.extend((byte / 127.5) - 1.0 for byte in digest)
            counter += 1
        return values[: self.dimension]


class FastEmbedLocalEmbeddingProvider:
    """Local embedding provider backed by FastEmbed. Suitable for free local/dev deployment."""

    def __init__(self, *, model_name: str = "BAAI/bge-small-zh-v1.5", dimension: int = 512) -> None:
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

    @property
    def model(self) -> object:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        # FastEmbed is synchronous; keep the API async-compatible with remote providers.
        vectors = [vector.tolist() for vector in self.model.embed(list(texts))]  # type: ignore[attr-defined]
        if vectors:
            self.dimension = len(vectors[0])
        return vectors


def embedding_provider_from_env() -> EmbeddingProvider:
    provider = os.getenv("RAG_EMBEDDING_PROVIDER", "fastembed_local").strip().lower()
    dimension = int(os.getenv("RAG_EMBEDDING_DIMENSION", "512"))
    if provider == "local_hash":
        return LocalHashEmbeddingProvider(dimension=dimension)
    if provider == "fastembed_local":
        return FastEmbedLocalEmbeddingProvider(
            model_name=os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
            dimension=dimension,
        )
    if provider != "openai_compatible":
        raise ValueError(f"Unsupported RAG_EMBEDDING_PROVIDER: {provider}")
    return OpenAICompatibleEmbeddingProvider(
        api_key=os.getenv("RAG_EMBEDDING_API_KEY", ""),
        model=os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
        base_url=os.getenv("RAG_EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
        dimension=dimension,
        timeout_seconds=float(os.getenv("RAG_EMBEDDING_TIMEOUT_SECONDS", "120")),
    )
