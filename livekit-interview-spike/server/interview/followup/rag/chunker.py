from __future__ import annotations

import hashlib
import re

from interview.followup.rag.models import MethodologyChunk, MethodologySource


_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？.!?])\s+|\n{2,}")
_RAG_CHUNK_HEADING_RE = re.compile(r"(?=^##\s+RAG\s+Chunk\s+\d+\b)", flags=re.MULTILINE | re.IGNORECASE)
_PRESEGMENTED_MAX_CHARS = 3200
_MIN_TRAILING_CHARS = 180


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
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if not text:
        return []
    rag_chunks = _split_by_rag_chunk_headings(text)
    if rag_chunks:
        return rag_chunks

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
    chunks = [text[index : index + chunk_size].strip() for index in range(0, len(text), chunk_size)]
    if len(chunks) > 1 and len(chunks[-1]) < _MIN_TRAILING_CHARS:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()
    return chunks


def _split_by_rag_chunk_headings(text: str) -> list[str]:
    sections = [section.strip() for section in _RAG_CHUNK_HEADING_RE.split(text) if section.strip()]
    rag_sections = [section for section in sections if re.match(r"^##\s+RAG\s+Chunk\s+\d+\b", section, flags=re.IGNORECASE)]
    if not rag_sections:
        return []
    chunks: list[str] = []
    for section in rag_sections:
        section = _strip_rag_section_noise(section)
        if not section:
            continue
        chunks.extend(_split_oversized_text(re.sub(r"\s+", " ", section).strip(), _PRESEGMENTED_MAX_CHARS))
    return chunks


def _strip_rag_section_noise(section: str) -> str:
    section = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL)
    section = re.sub(r"^##\s+RAG\s+Chunk\s+\d+\s*", "", section, flags=re.IGNORECASE).strip()
    section = re.sub(r"```(?:yaml|yml)\s+.*?chunk_id:.*?```\s*", "", section, flags=re.DOTALL | re.IGNORECASE)
    return section


def _tail(text: str, size: int) -> str:
    if size <= 0 or not text:
        return ""
    return text[-size:].strip()


def _stable_chunk_id(source_id: str, ordinal: int, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{source_id}:{ordinal}:{digest}"
