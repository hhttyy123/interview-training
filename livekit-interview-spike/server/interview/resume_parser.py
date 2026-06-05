from __future__ import annotations


MAX_RESUME_CHARS = 12000


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("缺少 pypdf 依赖，请运行 pip install pypdf") from error

    from io import BytesIO

    reader = PdfReader(BytesIO(file_bytes))
    chunks: list[str] = []
    for page in reader.pages[:8]:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()[:MAX_RESUME_CHARS]


def summarize_resume_text(text: str) -> dict[str, object]:
    clean = text.strip()[:MAX_RESUME_CHARS]
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    project_lines = [line for line in lines if any(word in line for word in ("项目", "负责", "实习", "经历", "成果", "指标"))][:12]
    skill_lines = [line for line in lines if any(word in line.lower() for word in ("技能", "python", "sql", "react", "产品", "运营", "数据"))][:8]
    return {
        "text": clean,
        "summary": "；".join(project_lines[:3]) or clean[:160],
        "projectHighlights": project_lines,
        "skillHighlights": skill_lines,
        "charCount": len(clean),
    }
