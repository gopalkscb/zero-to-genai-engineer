"""Dispatcher: route file bytes to the correct parser."""

from __future__ import annotations

from pathlib import Path

from app.graph.state import DocumentIR, SourceFormat
from app.parsing.html_parser import parse_html
from app.parsing.ipynb_parser import parse_ipynb
from app.parsing.pdf_parser import parse_pdf
from app.parsing.pptx_parser import parse_pptx
from app.parsing.text_parser import parse_text

EXTENSION_MAP: dict[str, SourceFormat] = {
    ".pdf": SourceFormat.PDF,
    ".pptx": SourceFormat.PPTX,
    ".html": SourceFormat.HTML,
    ".htm": SourceFormat.HTML,
    ".ipynb": SourceFormat.IPYNB,
    ".txt": SourceFormat.TEXT,
    ".md": SourceFormat.TEXT,
    ".transcript": SourceFormat.TRANSCRIPT,
}


def detect_format(filename: str) -> SourceFormat:
    ext = Path(filename).suffix.lower()
    return EXTENSION_MAP.get(ext, SourceFormat.TEXT)


def parse_upload(content: bytes, filename: str, source_id: str) -> DocumentIR:
    fmt = detect_format(filename)
    if fmt == SourceFormat.PDF:
        return parse_pdf(content, filename, source_id)
    if fmt == SourceFormat.PPTX:
        return parse_pptx(content, filename, source_id)
    if fmt == SourceFormat.HTML:
        return parse_html(content, filename, source_id)
    if fmt == SourceFormat.IPYNB:
        return parse_ipynb(content, filename, source_id)
    return parse_text(content, filename, source_id)
