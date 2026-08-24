"""Insert generated images into article markdown with Medium-style captions."""

from __future__ import annotations

import re

from app.graph.state import ImageAsset, ImageStatus

# Fake URLs the draft model sometimes invents, plus an optional italic caption line.
_OUTER_FENCE_OPEN = re.compile(r"^```(?:markdown|md)?\s*\n", re.IGNORECASE)
_OUTER_FENCE_CLOSE = re.compile(r"\n```\s*$")


def unwrap_outer_markdown_fence(text: str) -> str:
    """Draft models often wrap the whole article in a ```markdown fence."""
    stripped = (text or "").strip()
    if not stripped.startswith("```"):
        return stripped
    first_line, _, rest = stripped.partition("\n")
    lang = first_line[3:].strip().lower()
    if lang not in ("", "markdown", "md"):
        return stripped
    body = rest
    if _OUTER_FENCE_CLOSE.search(body):
        body = _OUTER_FENCE_CLOSE.sub("", body)
    return body.strip()


_PIPELINE_IMG = re.compile(
    r"!\[([^\]]*)\]\((/api/pipeline/[^)]+)\)(?:\n+\*[^*\n]+\*)?"
)
_FAKE_IMG = re.compile(
    r"!\[([^\]]*)\]\((https?://(?:example\.com|placehold(?:er|it)\.[^/\s)]+|via\.placeholder\.com)[^)]*)\)"
    r"(?:\n+\*[^*\n]+\*)?",
    re.IGNORECASE,
)


def figure_markdown(image: ImageAsset) -> str:
    caption = (image.caption or image.prompt or "Illustration").strip()
    url = image.url or image.local_path
    return f"![{caption}]({url})\n\n*{caption}*"


def _already_injected(markdown: str, images: list[ImageAsset]) -> bool:
    return any(img.url and img.url in markdown for img in images)


def inject_images(markdown: str, images: list[ImageAsset], *, replace: bool = False) -> str:
    ready = [
        img
        for img in images
        if img.status == ImageStatus.GENERATED and (img.url or img.local_path)
    ]
    text = unwrap_outer_markdown_fence(markdown or "")
    text = _FAKE_IMG.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not ready:
        return text
    if _already_injected(text, ready):
        if not replace:
            return text
        text = _PIPELINE_IMG.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

    lines = text.split("\n")
    h1_at = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    h2_at = [i for i, line in enumerate(lines) if line.startswith("## ")]
    insert_at: dict[int, list[ImageAsset]] = {}
    if h1_at is not None:
        insert_at.setdefault(h1_at, []).append(ready[0])
    extras = ready[1:]
    candidates = h2_at[1:] if len(h2_at) > 1 else h2_at
    if extras and candidates:
        used: set[int] = set()
        for idx, image in enumerate(extras):
            if len(candidates) == 1:
                pos = candidates[0]
            else:
                slot = int(round(idx * (len(candidates) - 1) / max(len(extras) - 1, 1)))
                pos = candidates[min(slot, len(candidates) - 1)]
            while pos in used and pos < (candidates[-1] if candidates else pos):
                pos += 1
            used.add(pos)
            insert_at.setdefault(pos, []).append(image)
    elif extras:
        insert_at.setdefault(h1_at or 0, []).extend(extras)

    out: list[str] = []
    for idx, line in enumerate(lines):
        out.append(line)
        for image in insert_at.get(idx, []):
            out.append("")
            out.append(figure_markdown(image))
    if h1_at is None and ready:
        out = [figure_markdown(ready[0]), "", *out]
    return "\n".join(out)
