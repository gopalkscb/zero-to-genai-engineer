"""Image generation client."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.llm.providers.bedrock_provider import BedrockProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.registry import get_model_for_stage


class ImageClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        if self.settings.llm_provider == "bedrock":
            self._provider = BedrockProvider(self.settings)
        else:
            self._provider = OpenAIProvider(self.settings)

    def generate(
        self,
        prompt: str,
        aspect_ratio: str | None = None,
        quality: str | None = None,
    ) -> bytes:
        model = get_model_for_stage("image", self.settings)
        return self._provider.generate_image(
            model=model,
            prompt=prompt,
            aspect_ratio=aspect_ratio or self.settings.image_aspect_ratio,
            quality=quality or self.settings.image_quality,
        )

    def save(self, image_bytes: bytes, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image_bytes)
        return str(path)

    def review(self, image_bytes: bytes, purpose: str) -> dict:
        reviewer = getattr(self._provider, "review_image", None)
        if reviewer is None:
            return {"pass": True, "notes": "Image review is not available on this provider.", "retry_prompt": ""}
        model = get_model_for_stage("reviewer_style", self.settings)
        return reviewer(model, image_bytes, purpose)
