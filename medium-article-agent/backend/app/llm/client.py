"""Provider-agnostic LLM client."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from app.config import Settings, get_settings
from app.llm.providers.bedrock_provider import BedrockProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.registry import Stage, get_model_for_stage


class LLMClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        if self.settings.llm_provider == "bedrock":
            self._provider = BedrockProvider(self.settings)
        else:
            self._provider = OpenAIProvider(self.settings)

    def complete(
        self,
        stage: Stage,
        messages: list[dict[str, str]],
        structured_schema: Type[BaseModel] | None = None,
        temperature: float = 0.7,
    ) -> str | BaseModel:
        model = get_model_for_stage(stage, self.settings)
        return self._provider.complete(
            model=model,
            messages=messages,
            structured_schema=structured_schema,
            temperature=temperature,
        )
