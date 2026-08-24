"""Plain text / transcript parser. Headings keep their level; lists stay lists."""

from __future__ import annotations

from pathlib import Path

from app.graph.state import Block, BlockType, DocumentIR, SourceFormat
from app.parsing.normalize import make_block_id


def _classify(para: str) -> tuple[BlockType, str, dict]:
    raw = para.strip()
    if not raw:
        return BlockType.PARAGRAPH, "", {}
    if raw.startswith("#"):
        hashes = len(raw) - len(raw.lstrip("#"))
        return BlockType.HEADING, raw.lstrip("#").strip(), {"heading_level": hashes, "raw": raw.split("\n", 1)[0]}
    lines = [ln.rstrip() for ln in raw.splitlines() if ln.strip()]
    if lines and all(ln.lstrip()[:1] in {"-", "*", "•"} or (len(ln.lstrip()) > 2 and ln.lstrip()[0].isdigit()) for ln in lines):
        return BlockType.LIST, raw, {}
    if raw.startswith("```") or (len(lines) > 1 and all("    " in ln[:4] or ln.startswith("\t") for ln in lines[1:])):
        return BlockType.CODE, raw.strip("`").strip(), {}
    if raw.startswith(">"):
        return BlockType.QUOTE, raw.lstrip("> ").strip(), {}
    return BlockType.PARAGRAPH, raw, {}


def parse_text(content: bytes, filename: str, source_id: str) -> DocumentIR:
    text = content.decode("utf-8", errors="replace")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    fmt = SourceFormat.TRANSCRIPT if "transcript" in filename.lower() else SourceFormat.TEXT
    warnings: list[str] = []
    blocks: list[Block] = []
    for idx, para in enumerate(paragraphs):
        btype, clean, meta = _classify(para)
        if not clean:
            continue
        blocks.append(
            Block(
                block_id=make_block_id(source_id, None, idx),
                source_id=source_id,
                source_format=fmt,
                block_type=btype,
                text=clean,
                order=idx + 1,
                page_or_slide=None,
                metadata=meta,
            )
        )

    if not blocks:
        warnings.append("empty text file")
        blocks.append(
            Block(
                block_id=make_block_id(source_id, None, 0),
                source_id=source_id,
                source_format=fmt,
                block_type=BlockType.METADATA,
                text=f"[No extractable content from {filename}]",
                order=1,
            )
        )

    char_count = sum(len(b.text) for b in blocks)
    return DocumentIR(
        source_id=source_id,
        source_format=fmt,
        filename=filename,
        blocks=blocks,
        char_count=char_count,
        block_count=len(blocks),
        warnings=warnings,
    )


def parse_text_file(path: Path, source_id: str) -> DocumentIR:
    return parse_text(path.read_bytes(), path.name, source_id)
