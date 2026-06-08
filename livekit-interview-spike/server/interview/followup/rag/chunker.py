from __future__ import annotations

import hashlib
import re

from interview.followup.rag.models import MethodologyChunk, MethodologySource


_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？.!?])\s+|\n{2,}")


def chunk_methodology_source(
    source: MethodologySource,
    *,
    chunk_size: int = 900,
    chunk_overlap: int = 120,
) -> list[MethodologyChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must not be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = _normalize_text(source.content)
    chunks = _chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return [
        MethodologyChunk(
            chunk_id=_stable_chunk_id(source.source_id, ordinal, chunk),
            source_id=source.source_id,
            title=source.title,
            text=chunk,
            ordinal=ordinal,
            source_type=source.source_type,
            source_url=source.source_url,
            license_note=source.license_note,
            metadata=dict(source.metadata),
        )
        for ordinal, chunk in enumerate(chunks)
    ]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if not text:
        return []

    sentences = [part.strip() for part in _SENTENCE_BOUNDARY_RE.split(text) if part.strip()]
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not current:
            current = sentence
            continue
        if len(current) + 1 + len(sentence) <= chunk_size:
            current = f"{current} {sentence}"
            continue
        chunks.extend(_split_oversized_text(current, chunk_size))
        current = _tail(current, chunk_overlap)
        current = f"{current} {sentence}".strip() if current else sentence

    if current:
        chunks.extend(_split_oversized_text(current, chunk_size))

    return [chunk for chunk in chunks if chunk]


def _split_oversized_text(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[index : index + chunk_size].strip() for index in range(0, len(text), chunk_size)]


def _tail(text: str, size: int) -> str:
    if size <= 0 or not text:
        return ""
    return text[-size:].strip()


def _stable_chunk_id(source_id: str, ordinal: int, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{source_id}:{ordinal}:{digest}"
