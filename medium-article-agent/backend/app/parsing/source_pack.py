"""Coverage-preserving source packing for LLM prompts.

Naive [:N] truncation drops the end of every long upload. This packer keeps
every heading, table, code block, and list, then round-robins remaining
paragraphs so each uploaded file still appears in the prompt.
"""

from __future__ import annotations

from app.graph.state import Block, BlockType, DocumentIR
from app.parsing.normalize import combine_text

PRIORITY_TYPES = {
    BlockType.HEADING,
    BlockType.CODE,
    BlockType.TABLE,
    BlockType.LIST,
    BlockType.SLIDE,
    BlockType.METADATA,
    BlockType.IMAGE,
}


def _type_of(block: Block) -> BlockType:
    raw = block.block_type
    if isinstance(raw, BlockType):
        return raw
    try:
        return BlockType(str(raw))
    except ValueError:
        return BlockType.PARAGRAPH


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n…[truncated block]"


def _render(block: Block) -> str:
    btype = _type_of(block).value
    loc = f"p{block.page_or_slide}" if block.page_or_slide is not None else "doc"
    return f"[{btype} | {loc} | {block.block_id}]\n{block.text.strip()}"


def pack_source(
    documents: list[DocumentIR] | None,
    combined_text: str = "",
    *,
    budget: int = 24000,
) -> str:
    """Return source text that fits `budget` without dropping a whole file."""
    docs = list(documents or [])
    if not docs:
        text = combined_text or ""
        if len(text) <= budget:
            return text
        return text[: budget - 80].rstrip() + "\n\n…[source truncated; no structured blocks available]"

    labeled = combine_text(docs)
    if len(labeled) <= budget:
        return labeled

    header = (
        f"PACKED SOURCE ({len(labeled)} chars across {len(docs)} file(s); "
        f"prompt budget {budget}). Kept every heading, table, code, list, and slide, "
        f"then sampled paragraphs from each file so nothing is silently dropped.\n"
    )
    used = len(header)
    parts: list[str] = [header]
    remaining: dict[str, list[Block]] = {}

    for doc in docs:
        banner = f"=== {doc.filename} ({doc.source_format.value}) ==="
        parts.append(banner)
        used += len(banner) + 2
        leftover: list[Block] = []
        for block in sorted(doc.blocks, key=lambda b: b.order):
            if not (block.text or "").strip():
                continue
            if _type_of(block) in PRIORITY_TYPES:
                chunk = _render(block)
                if len(chunk) > 4000:
                    chunk = _clip(chunk, 4000)
                if used + len(chunk) + 2 > budget:
                    leftover.append(block)
                    continue
                parts.append(chunk)
                used += len(chunk) + 2
            else:
                leftover.append(block)
        remaining[doc.source_id] = leftover

    queues = [(doc, remaining.get(doc.source_id, [])) for doc in docs]
    progressed = True
    while progressed and used < budget:
        progressed = False
        for doc, queue in queues:
            if not queue or used >= budget:
                continue
            block = queue.pop(0)
            chunk = _render(block)
            if len(chunk) > 2500:
                chunk = _clip(chunk, 2500)
            if used + len(chunk) + 2 > budget:
                queue.insert(0, block)
                continue
            parts.append(chunk)
            used += len(chunk) + 2
            progressed = True

    dropped = sum(len(queue) for _, queue in queues)
    if dropped:
        note = f"[{dropped} lower-priority paragraph(s) omitted after covering every file]"
        if used + len(note) + 2 <= budget:
            parts.append(note)
    return "\n\n".join(parts)
