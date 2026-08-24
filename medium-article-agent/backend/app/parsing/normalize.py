"""Normalize parsed blocks: global order, labeled combine, parse reports."""

from __future__ import annotations

from collections import Counter

from app.graph.state import Block, BlockType, DocumentIR, SourceFormat


def make_block_id(source_id: str, page_or_slide: int | None, index: int) -> str:
    """Stable id like pdf1-p3-b2."""
    page_part = f"p{page_or_slide}" if page_or_slide is not None else "p0"
    return f"{source_id}-{page_part}-b{index}"


def normalize_documents(documents: list[DocumentIR]) -> list[DocumentIR]:
    """Assign global order across all documents and recompute block_ids."""
    global_order = 0
    normalized: list[DocumentIR] = []

    for doc in documents:
        new_blocks: list[Block] = []
        for local_idx, block in enumerate(doc.blocks):
            global_order += 1
            new_blocks.append(
                Block(
                    block_id=make_block_id(
                        doc.source_id,
                        block.page_or_slide,
                        local_idx,
                    ),
                    source_id=doc.source_id,
                    source_format=doc.source_format,
                    block_type=block.block_type,
                    text=block.text,
                    order=global_order,
                    page_or_slide=block.page_or_slide,
                    metadata=block.metadata,
                )
            )
        char_count = sum(len(b.text) for b in new_blocks)
        normalized.append(
            DocumentIR(
                source_id=doc.source_id,
                source_format=doc.source_format,
                filename=doc.filename,
                blocks=new_blocks,
                char_count=char_count,
                block_count=len(new_blocks),
                warnings=list(doc.warnings or []),
            )
        )
    return normalized


def _locator(block: Block) -> str:
    if block.page_or_slide is None:
        loc = "doc"
    else:
        loc = f"page {block.page_or_slide}" if block.source_format == SourceFormat.PDF else f"slide {block.page_or_slide}"
        if block.source_format == SourceFormat.IPYNB:
            loc = f"cell {block.page_or_slide}"
    btype = block.block_type.value if hasattr(block.block_type, "value") else str(block.block_type)
    return f"[{btype} | {loc} | {block.block_id}]"


def combine_text(documents: list[DocumentIR]) -> str:
    """Lossless labeled dump. Every block keeps type, locator, and id."""
    parts: list[str] = []
    for doc in documents:
        fmt = doc.source_format.value if hasattr(doc.source_format, "value") else str(doc.source_format)
        parts.append(f"=== {doc.filename} ({fmt}) · {doc.block_count} blocks · {doc.char_count} chars ===")
        for warning in doc.warnings or []:
            parts.append(f"[parse warning] {warning}")
        for block in sorted(doc.blocks, key=lambda b: b.order):
            text = (block.text or "").strip()
            if not text:
                continue
            parts.append(f"{_locator(block)}\n{text}")
    return "\n\n".join(parts)


def summarize_documents(documents: list[DocumentIR]) -> dict:
    files: list[dict] = []
    warnings: list[str] = []
    total_chars = 0
    total_blocks = 0
    by_type: Counter[str] = Counter()
    for doc in documents:
        type_counts: Counter[str] = Counter()
        for block in doc.blocks:
            key = block.block_type.value if hasattr(block.block_type, "value") else str(block.block_type)
            type_counts[key] += 1
            by_type[key] += 1
        pages = {b.page_or_slide for b in doc.blocks if b.page_or_slide is not None}
        item = {
            "filename": doc.filename,
            "format": doc.source_format.value if hasattr(doc.source_format, "value") else str(doc.source_format),
            "chars": doc.char_count,
            "blocks": doc.block_count,
            "pages": len(pages),
            "by_type": dict(type_counts),
            "warnings": list(doc.warnings or []),
        }
        files.append(item)
        total_chars += doc.char_count
        total_blocks += doc.block_count
        for warning in doc.warnings or []:
            warnings.append(f"{doc.filename}: {warning}")
    return {
        "files": files,
        "total_chars": total_chars,
        "total_blocks": total_blocks,
        "by_type": dict(by_type),
        "warnings": warnings,
        "packed": False,
    }
