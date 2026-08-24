"""Jupyter notebook parser: markdown, code, AND cell outputs."""

from __future__ import annotations

import json

import nbformat

from app.graph.state import Block, BlockType, DocumentIR, SourceFormat
from app.parsing.normalize import make_block_id


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(str(part) for part in value)
    return str(value)


def _output_text(output: dict) -> str:
    kind = output.get("output_type") or ""
    if kind == "stream":
        return _as_text(output.get("text")).strip()
    if kind in ("execute_result", "display_data"):
        data = output.get("data") or {}
        for key in ("text/plain", "text/markdown", "text/html", "text/latex"):
            if key in data:
                text = _as_text(data[key]).strip()
                if text:
                    return text
        return ""
    if kind == "error":
        ename = output.get("ename") or "Error"
        evalue = output.get("evalue") or ""
        tb = _as_text(output.get("traceback") or "")
        # Tracebacks can be huge; keep the error identity and a tail.
        tail = tb[-1500:] if tb else ""
        return f"{ename}: {evalue}\n{tail}".strip()
    return ""


def parse_ipynb(content: bytes, filename: str, source_id: str) -> DocumentIR:
    nb = nbformat.reads(content.decode("utf-8", errors="replace"), as_version=4)
    blocks: list[Block] = []
    warnings: list[str] = []
    order = 0

    for cell_idx, cell in enumerate(nb.cells, start=1):
        cell_type = cell.get("cell_type", "code")
        source = _as_text(cell.get("source", "")).strip()
        local_idx = 0

        if source:
            order += 1
            local_idx += 1
            if cell_type == "markdown":
                btype = BlockType.HEADING if source.lstrip().startswith("#") else BlockType.PARAGRAPH
            elif cell_type == "code":
                btype = BlockType.CODE
            else:
                btype = BlockType.METADATA
            blocks.append(
                Block(
                    block_id=make_block_id(source_id, cell_idx, local_idx),
                    source_id=source_id,
                    source_format=SourceFormat.IPYNB,
                    block_type=btype,
                    text=source,
                    order=order,
                    page_or_slide=cell_idx,
                    metadata={"cell_type": cell_type, "kind": "source"},
                )
            )

        outputs = list(cell.get("outputs") or [])
        out_parts: list[str] = []
        for out in outputs:
            raw = out if isinstance(out, dict) else dict(out)
            text = _output_text(raw)
            if text:
                out_parts.append(text)
        if out_parts:
            order += 1
            local_idx += 1
            blocks.append(
                Block(
                    block_id=make_block_id(source_id, cell_idx, local_idx),
                    source_id=source_id,
                    source_format=SourceFormat.IPYNB,
                    block_type=BlockType.CODE,
                    text="\n".join(out_parts),
                    order=order,
                    page_or_slide=cell_idx,
                    metadata={"cell_type": cell_type, "kind": "output"},
                )
            )
        elif cell_type == "code" and not source and not outputs:
            warnings.append(f"cell {cell_idx}: empty code cell")

    if not blocks:
        warnings.append("no extractable notebook cells")
        blocks.append(
            Block(
                block_id=make_block_id(source_id, 1, 0),
                source_id=source_id,
                source_format=SourceFormat.IPYNB,
                block_type=BlockType.METADATA,
                text=f"[No extractable content from {filename}]",
                order=1,
                page_or_slide=1,
            )
        )

    char_count = sum(len(b.text) for b in blocks)
    return DocumentIR(
        source_id=source_id,
        source_format=SourceFormat.IPYNB,
        filename=filename,
        blocks=blocks,
        char_count=char_count,
        block_count=len(blocks),
        warnings=warnings,
    )


def build_sample_ipynb() -> bytes:
    """Inline fixture helper for tests."""
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": "# Sample Notebook\n\nThis is a test cell.",
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": "print('hello world')",
                "outputs": [],
                "execution_count": None,
            },
        ],
    }
    return json.dumps(nb).encode("utf-8")


def build_sample_ipynb_with_output() -> bytes:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "source": "print(50257)",
                "outputs": [
                    {"output_type": "stream", "name": "stdout", "text": ["50257\n"]},
                ],
                "execution_count": 1,
            }
        ],
    }
    return json.dumps(nb).encode("utf-8")
