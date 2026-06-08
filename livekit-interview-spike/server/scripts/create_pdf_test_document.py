from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


OUTPUT = Path(__file__).resolve().parents[1] / "data" / "docs" / "methodology-text-layer-test.pdf"


PDF_LINES = [
    "Interview methodology PDF test document",
    "",
    "This PDF has a real text layer and is generated without extra dependencies.",
    "It is used to test whether pypdf can extract text from PDF files before RAG ingestion.",
    "",
    "Section 1: STAR and BEI evidence collection",
    "A structured interview should collect Situation, Task, Action and Result evidence.",
    "If a candidate only says the team finished a project, ask about personal contribution.",
    "If a candidate only says the result was good, ask about metrics, feedback and attribution.",
    "",
    "Section 2: Pressure attribution probe",
    "Pressure questions should challenge evidence quality, not attack the candidate.",
    "Ask whether the result would still happen without the candidate's action.",
    "Ask whether other factors could explain the metric change.",
    "",
    "Section 3: Technical deep dive",
    "Technical interviews should inspect constraints, tradeoffs, validation and failure handling.",
    "Do not only ask terminology questions. Anchor the probe in a real project decision.",
    "",
    "Section 4: Business case",
    "Business case probes should inspect goal definition, user segmentation, metrics and risks.",
    "A strong answer explains assumptions, alternatives, priority and validation plan.",
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Font"),
                            NameObject("/Subtype"): NameObject("/Type1"),
                            NameObject("/BaseFont"): NameObject("/Helvetica"),
                        }
                    )
                }
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(_content_stream(PDF_LINES).encode("latin-1"))
    page[NameObject("/Contents")] = stream
    writer.add_metadata(
        {
            "/Title": "Methodology Text Layer Test",
            "/Subject": "RAG PDF parsing test document",
        }
    )
    with OUTPUT.open("wb") as file:
        writer.write(file)
    print(OUTPUT)


def _content_stream(lines: list[str]) -> str:
    escaped_lines = [_escape_pdf_text(line) for line in lines]
    commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for line in escaped_lines:
        commands.append(f"({line}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands)


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


if __name__ == "__main__":
    main()
