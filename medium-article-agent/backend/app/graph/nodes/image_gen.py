"""Image generation node."""

from __future__ import annotations

import re
from pathlib import Path

from app.config import get_settings
from app.graph.images import inject_images
from app.graph.runtime import report
from app.graph.state import AgentState, ImageAsset, ImageStatus, LogEntry, LogLevel
from app.llm.image_client import ImageClient


_BANNED_PROMPT = ("abstract illustration", "abstract image", "conceptual image", "visual representation")

_EDITORIAL_RULES = (
    "Editorial magazine illustration, 16:9, cinematic lighting. "
    "No letters, no words, no watermarks, no logos. "
    "Do not make an abstract color field or a stock photo of a person at a laptop. "
    "The reader must understand the idea in two seconds."
)


def _caption_for(index: int, heading: str) -> str:
    if index == 0:
        return "Cover illustration. AI-generated."
    clean = (heading or "Section visual").strip().rstrip(".")
    return f"{clean}. AI-generated."


def editorial_prompt(heading: str, thesis: str, planned: str = "", cover: bool = False) -> str:
    """Build a figure prompt a reader can actually parse. Abstract blobs fail this test."""
    planned = (planned or "").strip()
    lowered = planned.lower()
    usable_plan = bool(planned) and not any(banned in lowered for banned in _BANNED_PROMPT)
    if usable_plan:
        scene = planned
    elif cover:
        scene = (
            f"Cover metaphor for a Medium essay about {heading}. "
            f"Show one concrete object that stands for: {thesis or heading}."
        )
    else:
        scene = (
            f"A clear physical metaphor or simple diagram of {heading}, "
            f"in service of: {thesis or heading}."
        )
    return f"{_EDITORIAL_RULES} {scene}"


def _headings(markdown: str, plan_title: str, outline: list[str]) -> list[str]:
    found = re.findall(r"^##\s+(.+)$", markdown or "", re.M)
    titles = [plan_title] + (found or outline)
    return [t.strip() for t in titles if t and t.strip()]


def _dynamic_count(settings, headings: list[str], source_images: int) -> int:
    needed = 1 + max(1, (len(headings) - 1) // 2)
    target = max(settings.image_count, needed)
    return max(1, min(settings.image_count_max, target) - source_images)


def _harvest_uploads(state: AgentState, run_id: str) -> list[ImageAsset]:
    images: list[ImageAsset] = []
    settings = get_settings()
    idx = 0
    for item in state.get("uploaded_files") or []:
        name = str(item.get("filename") or "")
        suffix = Path(name).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        content = item.get("content") or b""
        if not content:
            continue
        idx += 1
        image_id = f"src_{idx}"
        out = Path(settings.data_dir) / "runs" / run_id / "images" / f"{image_id}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content if isinstance(content, (bytes, bytearray)) else bytes(content))
        images.append(
            ImageAsset(
                image_id=image_id,
                prompt=f"Uploaded source figure {name}",
                caption=f"Source figure from {name}",
                url=f"/api/pipeline/{run_id}/images/{image_id}.png",
                local_path=str(out),
                status=ImageStatus.GENERATED,
            )
        )
    return images


def _prompts_for(headings: list[str], plan_prompts: list[str], count: int, thesis: str) -> list[tuple[str, str]]:
    slots: list[tuple[str, str]] = []
    for idx in range(count):
        heading = headings[idx] if idx < len(headings) else headings[-1] if headings else "the article"
        planned = plan_prompts[idx] if idx < len(plan_prompts) else ""
        prompt = editorial_prompt(heading, thesis, planned, cover=(idx == 0))
        slots.append((prompt, _caption_for(idx, heading)))
    return slots


def image_gen_node(state: AgentState) -> dict:
    settings = get_settings()
    client = ImageClient(settings)
    run_id = state.get("run_id", "unknown")
    plan = state.get("plan")
    if isinstance(plan, dict):
        title = plan.get("title") or ""
        thesis = plan.get("thesis") or title
        prompts = list(plan.get("image_prompts") or [])
        outline = [s.get("title", "") if isinstance(s, dict) else getattr(s, "title", "") for s in (plan.get("pyramid_outline") or [])]
    elif plan:
        title = plan.title
        thesis = plan.thesis or plan.title
        prompts = list(plan.image_prompts)
        outline = [s.title for s in plan.pyramid_outline]
    else:
        title = thesis = ""
        prompts = []
        outline = []

    draft = state.get("draft_markdown", "") or state.get("final_markdown", "")
    headings = _headings(draft, title or thesis, outline)
    harvested = _harvest_uploads(state, run_id)
    ai_count = _dynamic_count(settings, headings, len(harvested))
    slots = _prompts_for(headings, prompts, ai_count, thesis)

    images: list[ImageAsset] = list(harvested)
    logs: list[LogEntry] = [
        report(
            run_id,
            "image_gen",
            f"Starting image generation: {ai_count} HD figure(s). Each can take 1–2 minutes.",
        )
    ]
    if harvested:
        logs.append(
            LogEntry(
                node="image_gen",
                level=LogLevel.INFO,
                message=f"Attached {len(harvested)} source screenshot(s)",
            )
        )

    for idx, (prompt, caption) in enumerate(slots):
        image_id = f"img_{idx + 1}"
        logs.append(
            report(
                run_id,
                "image_gen",
                f"Generating figure {idx + 1}/{len(slots)} ({image_id}, HD). The pipeline is not stuck on Draft.",
            )
        )
        asset = ImageAsset(
            image_id=image_id,
            prompt=prompt,
            caption=caption,
            aspect_ratio=settings.image_aspect_ratio,
            url=f"/api/pipeline/{run_id}/images/{image_id}.png",
            status=ImageStatus.PENDING,
        )
        try:
            # Generate only. Art-direction review and redraw live in their own nodes
            # so a fail can loop without regenerating every figure.
            img_bytes = client.generate(prompt)
            out_path = Path(settings.data_dir) / "runs" / run_id / "images" / f"{image_id}.png"
            local_path = client.save(img_bytes, out_path)
            asset.local_path = local_path
            asset.status = ImageStatus.GENERATED
            asset.review_passed = False
            asset.review_notes = "Awaiting art-direction review."
            logs.append(
                LogEntry(
                    node="image_gen",
                    level=LogLevel.INFO,
                    message=f"Generated image {image_id}",
                )
            )
        except Exception as exc:
            asset.status = ImageStatus.SKIPPED_ERROR
            asset.review_passed = False
            asset.review_notes = str(exc)
            logs.append(
                LogEntry(
                    node="image_gen",
                    level=LogLevel.WARNING,
                    message=f"Skipped image {image_id}: {exc}",
                )
            )
        images.append(asset)

    final = state.get("final_markdown", "")
    if any(img.status == ImageStatus.GENERATED for img in images):
        draft = inject_images(draft, images, replace=True)
        if final:
            final = inject_images(final, images, replace=True)

    result = {"images": images, "draft_markdown": draft, "logs": logs, "current_node": "image_gen"}
    if final:
        result["final_markdown"] = final
    return result
