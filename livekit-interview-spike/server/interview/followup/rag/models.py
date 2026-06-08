from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


MetadataValue = str | int | float | bool | list[str] | None


@dataclass(frozen=True)
class MethodologySource:
    """A professional interview-methodology source before chunking."""

    source_id: str
    title: str
    content: str
    source_type: str = "methodology"
    source_url: str = ""
    license_note: str = ""
    metadata: dict[str, MetadataValue] = field(default_factory=dict)


@dataclass(frozen=True)
class MethodologyChunk:
    """A searchable chunk stored in the vector database."""

    chunk_id: str
    source_id: str
    title: str
    text: str
    ordinal: int
    source_type: str = "methodology"
    source_url: str = ""
    license_note: str = ""
    metadata: dict[str, MetadataValue] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalQuery:
    query_text: str
    limit: int = 6
    strategy_id: str = ""
    strategy_category: str = ""
    question_style_id: str = ""
    interview_style_id: str = ""
    role_family: str = ""
    competency_archetypes: tuple[str, ...] = ()
    evidence_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    chunk: MethodologyChunk
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestionReport:
    source_count: int
    chunk_count: int
    collection: str
