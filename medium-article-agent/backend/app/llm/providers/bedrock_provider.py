"""AWS Bedrock LLM provider."""

from __future__ import annotations

import json
from typing import Type

import boto3
from pydantic import BaseModel

from app.config import Settings


class BedrockProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def _resolve_model(self, model: str) -> str:
        if model.startswith("bedrock:"):
            return model.split(":", 1)[1]
        return model or self.settings.bedrock_model_draft

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        structured_schema: Type[BaseModel] | None = None,
        temperature: float = 0.7,
    ) -> str | BaseModel:
        model_id = self._resolve_model(model)
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts = [m["content"] for m in messages if m["role"] != "system"]
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": temperature,
            "system": "\n".join(system_parts) if system_parts else "",
            "messages": [{"role": "user", "content": "\n\n".join(user_parts)}],
        }
        if structured_schema:
            body["messages"][0]["content"] += (
                f"\n\nRespond with valid JSON matching: {json.dumps(structured_schema.model_json_schema())}"
            )

        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        text = payload.get("content", [{}])[0].get("text", "")

        if structured_schema:
            return structured_schema.model_validate(json.loads(text))
        return text

    def generate_image(
        self,
        model: str,
        prompt: str,
        aspect_ratio: str = "16:9",
        quality: str = "standard",
    ) -> bytes:
        # Bedrock image models vary by account; raise clear error if unavailable
        raise NotImplementedError(
            "Bedrock image generation requires model-specific setup (e.g. Titan Image). "
            "Use LLM_PROVIDER=openai for image generation or configure a Bedrock image model."
        )
