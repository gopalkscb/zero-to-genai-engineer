"""Art-direction review and bounded redraw. Separate from image_gen on purpose.

Production writing graphs treat the artist as its own loop (generate → critic →
redraw) with a hard cap. Bundling a one-shot retry inside generation hid failures
from the graph UI and could not iterate.
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.graph.images import inject_images
from app.graph.runtime import report
from app.graph.state import AgentState, ImageAsset, ImageStatus, LogEntry, LogLevel
from app.llm.image_client import ImageClient


def coerce_images(raw) -> list[ImageAsset]:
    images: list[ImageAsset] = []
    for item in raw or []:
        if isinstance(item, ImageAsset):
            images.append(item.model_copy())
        elif isinstance(item, dict):
            try:
                images.append(ImageAsset.model_validate(item))
            except Exception:
                continue
    return images


def is_source_upload(image: ImageAsset) -> bool:
    return image.image_id.startswith("src_")


def images_need_redraw(state: AgentState | dict) -> bool:
    for image in coerce_images(state.get("images")):
        if is_source_upload(image):
            continue
        if image.status != ImageStatus.GENERATED:
            continue
        if not image.review_passed:
            return True
    return False


def image_review_node(state: AgentState) -> dict:
    run_id = str(state.get("run_id") or "unknown")
    client = ImageClient()
    images = coerce_images(state.get("images"))
    logs: list[LogEntry] = [
        report(run_id, "image_review", "Vision-checking figures. This can take a minute.")
    ]
    failed = 0
    reviewed = 0

    for image in images:
        if image.status != ImageStatus.GENERATED:
            continue
        if is_source_upload(image):
            image.review_passed = True
            if not image.review_notes or image.review_notes.startswith("Awaiting"):
                image.review_notes = "Source upload; art-direction skipped."
            continue
        path = Path(image.local_path) if image.local_path else None
        if not path or not path.exists():
            # Missing bytes cannot be redrawn usefully. Do not loop forever.
            image.review_passed = True
            image.review_notes = "Image file missing; vision review skipped."
            logs.append(
                LogEntry(
                    node="image_review",
                    level=LogLevel.WARNING,
                    message=f"{image.image_id}: file missing, skipped vision review",
                )
            )
            continue
        try:
            review = client.review(path.read_bytes(), image.caption or image.prompt)
        except Exception as exc:
            image.review_passed = True
            image.review_notes = f"Vision review failed: {exc}"
            logs.append(
                LogEntry(
                    node="image_review",
                    level=LogLevel.WARNING,
                    message=f"{image.image_id}: vision review failed ({exc})",
                )
            )
            continue
        reviewed += 1
        image.review_passed = bool(review.get("pass"))
        image.review_notes = str(review.get("notes") or "").strip()
        retry = str(review.get("retry_prompt") or "").strip()
        if retry:
            image.redraw_prompt = retry
        if not image.review_passed:
            failed += 1
            logs.append(
                LogEntry(
                    node="image_review",
                    level=LogLevel.WARNING,
                    message=f"{image.image_id} rejected: {image.review_notes or 'unclear figure'}",
                )
            )
        else:
            logs.append(
                LogEntry(
                    node="image_review",
                    level=LogLevel.INFO,
                    message=f"{image.image_id} passed art direction",
                )
            )

    logs.append(
        LogEntry(
            node="image_review",
            level=LogLevel.INFO,
            message=f"Art-direction review: {reviewed} checked, {failed} rejected",
        )
    )
    return {"images": images, "logs": logs}


def image_redraw_node(state: AgentState) -> dict:
    settings = get_settings()
    client = ImageClient(settings)
    run_id = state.get("run_id", "unknown")
    images = coerce_images(state.get("images"))
    redrawn = 0
    count = int(state.get("image_redraw_count") or 0) + 1
    logs: list[LogEntry] = [
        report(run_id, "image_redraw", f"Redraw pass {count}. Each figure can take a minute.")
    ]

    for image in images:
        if is_source_upload(image) or image.review_passed:
            continue
        if image.status != ImageStatus.GENERATED:
            continue
        prompt = (image.redraw_prompt or image.prompt or "").strip()
        if not prompt:
            continue
        try:
            logs.append(
                report(
                    run_id,
                    "image_redraw",
                    f"Redrawing {image.image_id} (pass {count}).",
                )
            )
            img_bytes = client.generate(prompt)
            out_path = Path(settings.data_dir) / "runs" / run_id / "images" / f"{image.image_id}.png"
            image.local_path = client.save(img_bytes, out_path)
            image.prompt = prompt
            image.status = ImageStatus.GENERATED
            image.review_passed = False
            image.review_notes = "Awaiting art-direction review."
            redrawn += 1
            logs.append(
                LogEntry(
                    node="image_redraw",
                    level=LogLevel.INFO,
                    message=f"Redraw {count} regenerated {image.image_id}",
                )
            )
        except Exception as exc:
            image.status = ImageStatus.SKIPPED_ERROR
            image.review_passed = True
            image.review_notes = f"Redraw failed: {exc}"
            logs.append(
                LogEntry(
                    node="image_redraw",
                    level=LogLevel.WARNING,
                    message=f"Could not redraw {image.image_id}: {exc}",
                )
            )

    draft = state.get("draft_markdown", "") or ""
    final = state.get("final_markdown", "") or ""
    result: dict = {
        "images": images,
        "image_redraw_count": count,
        "logs": logs
        or [
            LogEntry(
                node="image_redraw",
                level=LogLevel.INFO,
                message=f"Redraw pass {count}: {redrawn} figure(s) regenerated",
            )
        ],
    }
    if any(img.status == ImageStatus.GENERATED for img in images):
        result["draft_markdown"] = inject_images(draft, images, replace=True)
        if final:
            result["final_markdown"] = inject_images(final, images, replace=True)
    return result
