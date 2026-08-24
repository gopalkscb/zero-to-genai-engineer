"""OpenAI LLM provider implementation."""

from __future__ import annotations

import json
from typing import Any, Type

from openai import OpenAI
from pydantic import BaseModel

from app.config import Settings


class OpenAIProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key or None)

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        structured_schema: Type[BaseModel] | None = None,
        temperature: float = 0.7,
    ) -> str | BaseModel:
        if structured_schema:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": structured_schema.__name__,
                        "schema": structured_schema.model_json_schema(),
                    },
                },
            )
            raw = response.choices[0].message.content or "{}"
            return structured_schema.model_validate(json.loads(raw))

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def generate_image(
        self,
        model: str,
        prompt: str,
        aspect_ratio: str = "16:9",
        quality: str = "standard",
    ) -> bytes:
        import base64

        import httpx

        # GPT image models reject response_format; dall-e-3 accepts url or b64.
        # Omit it and accept whichever payload the model returns.
        is_dalle = model.startswith("dall-e")
        kwargs: dict[str, Any] = {"model": model, "prompt": prompt, "n": 1}
        if is_dalle:
            kwargs["size"] = "1792x1024" if aspect_ratio == "16:9" else "1024x1024"
            if quality in ("standard", "hd"):
                kwargs["quality"] = quality
        else:
            kwargs["size"] = "1536x1024" if aspect_ratio == "16:9" else "1024x1024"
            kwargs["quality"] = {"standard": "medium", "hd": "high"}.get(quality, quality)

        # HD gpt-image-1 routinely takes 60–120s. Bound it so a hung HTTP
        # call cannot freeze the graph with no log forever.
        result = self.client.with_options(timeout=240.0).images.generate(**kwargs)
        if not result.data:
            raise RuntimeError("Image API returned no data")
        item = result.data[0]
        if item.b64_json:
            return base64.b64decode(item.b64_json)
        if item.url:
            response = httpx.get(item.url, timeout=60.0)
            response.raise_for_status()
            return response.content
        raise RuntimeError("Image response had neither b64_json nor url")

    def review_image(self, model: str, image_bytes: bytes, purpose: str) -> dict[str, Any]:
        import base64
        import json as json_lib

        payload = base64.b64encode(image_bytes).decode("ascii")
        response = self.client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are the art director for a Medium technical essay.\n"
                                f"This figure must explain: {purpose}\n\n"
                                "Reject abstract color blobs, random people at laptops, illegible mush, "
                                "misspelled text, watermarks, or generic stock.\n"
                                "Accept a clear metaphor or diagram a reader can parse in two seconds.\n"
                                "If you reject it, rewrite retry_prompt as a concrete scene with objects, "
                                "lighting, and composition. No letters in the image.\n"
                                "Return JSON with keys pass (boolean), notes (one sentence), "
                                "retry_prompt (a better no-text image prompt if pass is false)."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{payload}"},
                        },
                    ],
                }
            ],
        )
        raw = response.choices[0].message.content or "{}"
        data = json_lib.loads(raw)
        return {
            "pass": bool(data.get("pass")),
            "notes": str(data.get("notes") or "").strip(),
            "retry_prompt": str(data.get("retry_prompt") or "").strip(),
        }
