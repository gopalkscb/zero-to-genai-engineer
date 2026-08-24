"""LLM stage registry — maps pipeline stages to model IDs from env."""

from __future__ import annotations

from typing import Literal

from app.config import Settings, get_settings

Stage = Literal[
    "plan",
    "draft",
    "reviewer",
    "reviewer_technical",
    "reviewer_style",
    "reviewer_structure",
    "reviewer_grounding",
    "reviewer_reader",
    "rewrite",
    "rewrite_voice",
    "editor",
    "headline",
    "style",
    "final",
    "quiz",
    "image",
]


_REVIEWER_ALT_MAP = {
    "reviewer_technical": "model_reviewer_technical_alt",
    "reviewer_style": "model_reviewer_style_alt",
    "reviewer_structure": "model_reviewer_structure_alt",
    "reviewer_grounding": "model_reviewer_grounding_alt",
    "reviewer_reader": "model_reviewer_reader_alt",
}


def get_model_for_stage(stage: Stage, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if settings.diversity_provider and stage in _REVIEWER_ALT_MAP:
        alt = getattr(settings, _REVIEWER_ALT_MAP[stage], "")
        if alt:
            return alt

    mapping = {
        "plan": settings.model_plan,
        "draft": settings.model_draft,
        "reviewer": settings.model_reviewer,
        "reviewer_technical": settings.model_reviewer,
        "reviewer_style": settings.model_reviewer,
        "reviewer_structure": settings.model_reviewer,
        "reviewer_grounding": settings.model_reviewer,
        "reviewer_reader": settings.model_reviewer,
        "rewrite": settings.model_rewrite,
        "rewrite_voice": settings.model_rewrite,
        "editor": settings.model_final,
        "headline": settings.model_style,
        "style": settings.model_style,
        "final": settings.model_final,
        "quiz": settings.model_quiz,
        "image": settings.model_image,
    }
    return mapping.get(stage, settings.model_draft)
