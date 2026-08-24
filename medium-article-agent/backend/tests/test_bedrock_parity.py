"""Bedrock provider wiring. Live invoke is skipped without credentials."""

from __future__ import annotations

import os

import pytest

from app.config import Settings
from app.llm.providers.bedrock_provider import BedrockProvider
from app.llm.registry import get_model_for_stage


def test_bedrock_env_ids_override_openai_defaults():
    settings = Settings(
        llm_provider="bedrock",
        model_plan="gpt-4o-mini",
        model_draft="gpt-4o",
        bedrock_model_plan="us.anthropic.claude-plan",
        bedrock_model_draft="us.anthropic.claude-draft",
    )
    assert get_model_for_stage("plan", settings) == "us.anthropic.claude-plan"
    assert get_model_for_stage("draft", settings) == "us.anthropic.claude-draft"
    assert get_model_for_stage("reviewer", settings) == "us.anthropic.claude-draft"
    assert get_model_for_stage("image", settings) == settings.model_image


@pytest.mark.skipif(
    os.getenv("LLM_PROVIDER") != "bedrock",
    reason="Set LLM_PROVIDER=bedrock to run parity test",
)
def test_bedrock_provider_instantiates():
    settings = Settings(llm_provider="bedrock")
    provider = BedrockProvider(settings)
    assert provider.client is not None
