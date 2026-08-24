"""HTML parser: preserve headings, lists, code, and tables. Trafilatura is fallback only."""

from __future__ import annotations

import trafilatura
from bs4 import BeautifulSoup, Tag

from app.graph.state import Block, BlockType, DocumentIR, SourceFormat
from app.parsing.normalize import make_block_id

_SKIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "iframe"}
_BLOCK_TAGS = {
    "h1": BlockType.HEADING,
    "h2": BlockType.HEADING,
    "h3": BlockType.HEADING,
    "h4": BlockType.HEADING,
    "h5": BlockType.HEADING,
    "h6": BlockType.HEADING,
    "p": BlockType.PARAGRAPH,
    "li": BlockType.LIST,
    "pre": BlockType.CODE,
    "blockquote": BlockType.QUOTE,
}


def _table_markdown(table: Tag) -> str:
    lines: list[str] = []
    for tr in table.find_all("tr"):
        cells = [cell.get_text(" ", strip=True).replace("\n", " ") for cell in tr.find_all(["th", "td"])]
        if cells:
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _structured_blocks(html: str) -> list[tuple[BlockType, str, dict]]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_SKIP_TAGS):
        tag.decompose()
    found: list[tuple[BlockType, str, dict]] = []
    seen: set[int] = set()

    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "blockquote", "table"]):
        if id(el) in seen:
            continue
        if el.find_parent(_SKIP_TAGS):
            continue
        if el.name == "table":
            md = _table_markdown(el)
            for nested in el.find_all(True):
                seen.add(id(nested))
            seen.add(id(el))
            if md:
                found.append((BlockType.TABLE, md, {"kind": "table"}))
            continue
        if el.find_parent("table"):
            continue
        text = el.get_text("\n", strip=True) if el.name == "pre" else el.get_text(" ", strip=True)
        if not text:
            continue
        seen.add(id(el))
        meta = {}
        if el.name.startswith("h") and len(el.name) == 2:
            meta["heading_level"] = int(el.name[1])
        found.append((_BLOCK_TAGS[el.name], text, meta))
    return found


def _fallback_blocks(html: str) -> list[tuple[BlockType, str, dict]]:
    extracted = trafilatura.extract(html, include_comments=False, include_tables=True, include_formatting=True)
    if not extracted:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(_SKIP_TAGS):
            tag.decompose()
        extracted = soup.get_text(separator="\n", strip=True)
    paragraphs = [p.strip() for p in (extracted or "").split("\n\n") if p.strip()]
    out: list[tuple[BlockType, str, dict]] = []
    for para in paragraphs:
        btype = BlockType.HEADING if len(para) < 80 and para.isupper() else BlockType.PARAGRAPH
        out.append((btype, para, {}))
    return out


def parse_html(content: bytes, filename: str, source_id: str) -> DocumentIR:
    html = content.decode("utf-8", errors="replace")
    warnings: list[str] = []
    extracted = _structured_blocks(html)
    if sum(len(text) for _, text, _ in extracted) < 40:
        fallback = _fallback_blocks(html)
        if sum(len(text) for _, text, _ in fallback) > sum(len(text) for _, text, _ in extracted):
            warnings.append("structured HTML was thin; used article-extraction fallback")
            extracted = fallback

    blocks: list[Block] = []
    for idx, (btype, text, meta) in enumerate(extracted):
        blocks.append(
            Block(
                block_id=make_block_id(source_id, None, idx),
                source_id=source_id,
                source_format=SourceFormat.HTML,
                block_type=btype,
                text=text,
                order=idx + 1,
                page_or_slide=None,
                metadata=meta,
            )
        )

    if not blocks:
        warnings.append("no extractable HTML content")
        blocks.append(
            Block(
                block_id=make_block_id(source_id, None, 0),
                source_id=source_id,
                source_format=SourceFormat.HTML,
                block_type=BlockType.METADATA,
                text=f"[No extractable content from {filename}]",
                order=1,
            )
        )

    char_count = sum(len(b.text) for b in blocks)
    return DocumentIR(
        source_id=source_id,
        source_format=SourceFormat.HTML,
        filename=filename,
        blocks=blocks,
        char_count=char_count,
        block_count=len(blocks),
        warnings=warnings,
    )
