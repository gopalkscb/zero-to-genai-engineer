"""PDF parser using PyMuPDF: reading-order blocks, tables, and image placeholders."""

from __future__ import annotations

import pymupdf as fitz

from app.graph.state import Block, BlockType, DocumentIR, SourceFormat
from app.parsing.normalize import make_block_id


def _bbox(item) -> tuple[float, float, float, float] | None:
    raw = getattr(item, "bbox", None)
    if raw is None and isinstance(item, dict):
        raw = item.get("bbox")
    if raw is None:
        return None
    return (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))


def _inside_table(bbox: tuple[float, float, float, float] | None, tables: list[tuple[float, float, float, float]], pad: float = 3.0) -> bool:
    if bbox is None:
        return False
    x0, y0, x1, y1 = bbox
    for tx0, ty0, tx1, ty1 in tables:
        if x0 >= tx0 - pad and y0 >= ty0 - pad and x1 <= tx1 + pad and y1 <= ty1 + pad:
            return True
    return False


def _table_markdown(table) -> str:
    try:
        md = table.to_markdown()
        if md and md.strip():
            return md.strip()
    except Exception:
        pass
    try:
        rows = table.extract() or []
    except Exception:
        return ""
    lines: list[str] = []
    for row in rows:
        cells = [str(cell or "").replace("\n", " ").strip() for cell in row]
        if any(cells):
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _block_text(block: dict) -> tuple[str, float, bool, str]:
    """Return (text, max_font_size, is_bold, font_name)."""
    lines_out: list[str] = []
    max_size = 0.0
    bold = False
    font_name = ""
    for line in block.get("lines") or []:
        parts: list[str] = []
        for span in line.get("spans") or []:
            parts.append(span.get("text") or "")
            size = float(span.get("size") or 0)
            max_size = max(max_size, size)
            flags = int(span.get("flags") or 0)
            if flags & 16:
                bold = True
            font_name = font_name or str(span.get("font") or "")
        text = "".join(parts).rstrip()
        if text:
            lines_out.append(text)
    return "\n".join(lines_out).strip(), max_size, bold, font_name.lower()


def _classify_text(text: str, size: float, bold: bool, font: str) -> BlockType:
    stripped = text.strip()
    if not stripped:
        return BlockType.PARAGRAPH
    first = stripped.split("\n", 1)[0]
    if first[:1] in {"•", "·", "–", "-", "*"} or first[:2] in {"- ", "* "}:
        return BlockType.LIST
    if first[:3].rstrip().rstrip(".").isdigit() and (first[1:3] in {". ", ") "} or (len(first) > 2 and first[1] in ".)")):
        return BlockType.LIST
    mono = any(token in font for token in ("mono", "courier", "consolas", "code"))
    if mono and ("\n" in stripped or "=" in stripped or stripped.endswith((";", "{", "}"))):
        return BlockType.CODE
    if (size >= 13.5 or (bold and size >= 12)) and len(stripped) < 140 and not stripped.endswith((".", "?", "!")):
        return BlockType.HEADING
    if stripped.startswith(">") or (stripped.startswith('"') and stripped.endswith('"') and len(stripped) < 280):
        return BlockType.QUOTE
    return BlockType.PARAGRAPH


def parse_pdf(content: bytes, filename: str, source_id: str) -> DocumentIR:
    doc = fitz.open(stream=content, filetype="pdf")
    blocks: list[Block] = []
    warnings: list[str] = []
    order = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_index = page_num + 1
        local_idx = 0
        table_boxes: list[tuple[float, float, float, float]] = []
        page_had_text = False
        page_had_image = False

        try:
            finder = page.find_tables()
            tables = list(getattr(finder, "tables", None) or [])
        except Exception:
            tables = []

        for table in tables:
            md = _table_markdown(table)
            box = _bbox(table)
            if box:
                table_boxes.append(box)
            if not md:
                continue
            order += 1
            local_idx += 1
            page_had_text = True
            blocks.append(
                Block(
                    block_id=make_block_id(source_id, page_index, local_idx),
                    source_id=source_id,
                    source_format=SourceFormat.PDF,
                    block_type=BlockType.TABLE,
                    text=md,
                    order=order,
                    page_or_slide=page_index,
                    metadata={"kind": "table"},
                )
            )

        try:
            page_dict = page.get_text("dict") or {}
        except Exception:
            page_dict = {}

        for raw in page_dict.get("blocks") or []:
            btype = int(raw.get("type") or 0)
            box = _bbox(raw)
            if btype == 1:
                page_had_image = True
                if _inside_table(box, table_boxes):
                    continue
                width = int(raw.get("width") or (box[2] - box[0] if box else 0))
                height = int(raw.get("height") or (box[3] - box[1] if box else 0))
                order += 1
                local_idx += 1
                blocks.append(
                    Block(
                        block_id=make_block_id(source_id, page_index, local_idx),
                        source_id=source_id,
                        source_format=SourceFormat.PDF,
                        block_type=BlockType.IMAGE,
                        text=f"[Embedded image on page {page_index}, {width}x{height}px]",
                        order=order,
                        page_or_slide=page_index,
                        metadata={"kind": "image", "width": width, "height": height},
                    )
                )
                continue

            if _inside_table(box, table_boxes):
                continue
            text, size, bold, font = _block_text(raw)
            if not text:
                continue
            page_had_text = True
            order += 1
            local_idx += 1
            blocks.append(
                Block(
                    block_id=make_block_id(source_id, page_index, local_idx),
                    source_id=source_id,
                    source_format=SourceFormat.PDF,
                    block_type=_classify_text(text, size, bold, font),
                    text=text,
                    order=order,
                    page_or_slide=page_index,
                    metadata={"font_size": round(size, 1), "bold": bold},
                )
            )

        if not page_had_text:
            fallback = (page.get_text("text") or "").strip()
            if fallback:
                page_had_text = True
                for para in [p.strip() for p in fallback.split("\n\n") if p.strip()] or [fallback]:
                    order += 1
                    local_idx += 1
                    blocks.append(
                        Block(
                            block_id=make_block_id(source_id, page_index, local_idx),
                            source_id=source_id,
                            source_format=SourceFormat.PDF,
                            block_type=BlockType.PARAGRAPH,
                            text=para,
                            order=order,
                            page_or_slide=page_index,
                        )
                    )

        if not page_had_text and page_had_image:
            warnings.append(f"page {page_index}: image-only, no extractable text")
        elif not page_had_text and not page_had_image:
            warnings.append(f"page {page_index}: empty (no text or images)")
            order += 1
            local_idx += 1
            blocks.append(
                Block(
                    block_id=make_block_id(source_id, page_index, local_idx),
                    source_id=source_id,
                    source_format=SourceFormat.PDF,
                    block_type=BlockType.METADATA,
                    text=f"[Empty page {page_index}: no extractable text or images]",
                    order=order,
                    page_or_slide=page_index,
                    metadata={"empty_page": True},
                )
            )

    doc.close()
    if not blocks:
        warnings.append("no extractable text, tables, or images")
        blocks.append(
            Block(
                block_id=make_block_id(source_id, 1, 0),
                source_id=source_id,
                source_format=SourceFormat.PDF,
                block_type=BlockType.METADATA,
                text=f"[No extractable content from {filename}]",
                order=1,
                page_or_slide=1,
            )
        )

    char_count = sum(len(b.text) for b in blocks)
    return DocumentIR(
        source_id=source_id,
        source_format=SourceFormat.PDF,
        filename=filename,
        blocks=blocks,
        char_count=char_count,
        block_count=len(blocks),
        warnings=warnings,
    )
