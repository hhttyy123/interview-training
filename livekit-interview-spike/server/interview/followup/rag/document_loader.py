from __future__ import annotations

import hashlib
import re
from pathlib import Path

from pypdf import PdfReader

from interview.followup.rag.models import MetadataValue, MethodologySource


SUPPORTED_DOCUMENT_SUFFIXES = {".txt", ".md", ".markdown", ".pdf", ".docx"}


def load_methodology_documents(
    *,
    path: str | Path,
    source_type: str = "internal_note",
    license_note: str = "",
    metadata: dict[str, MetadataValue] | None = None,
) -> list[MethodologySource]:
    root = Path(path)
    files = _document_files(root)
    return [
        MethodologySource(
            source_id=_source_id(file),
            title=file.stem,
            content=_extract_text(file),
            source_type=source_type,
            source_url=str(file),
            license_note=license_note,
            metadata=dict(metadata or {}),
        )
        for file in files
        if _extract_text(file).strip()
    ]


def _document_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() not in SUPPORTED_DOCUMENT_SUFFIXES:
            raise ValueError(f"Unsupported document suffix: {path.suffix}")
        return [path]
    if not path.exists():
        raise FileNotFoundError(path)
    return sorted(
        file
        for file in path.rglob("*")
        if file.is_file() and file.suffix.lower() in SUPPORTED_DOCUMENT_SUFFIXES
    )


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return _normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix == ".docx":
        return _extract_docx_text(path)
    raise ValueError(f"Unsupported document suffix: {suffix}")


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = [page.extract_text() or "" for page in reader.pages]
    return _normalize_text("\n".join(parts))


def _extract_docx_text(path: Path) -> str:
    from docx import Document

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    table_cells: list[str] = []
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text.strip()
                if text:
                    table_cells.append(text)
    return _normalize_text("\n".join([*paragraphs, *table_cells]))


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _source_id(path: Path) -> str:
    resolved = str(path.resolve()).encode("utf-8", errors="ignore")
    digest = hashlib.sha1(resolved).hexdigest()[:12]
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", path.stem).strip("-").lower() or "document"
    return f"doc-{safe_stem}-{digest}"
