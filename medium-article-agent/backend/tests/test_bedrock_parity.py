"""Bedrock provider parity test (skipped without credentials)."""

from __future__ import annotations

import os

import pytest

from app.config import Settings
from app.llm.providers.bedrock_provider import BedrockProvider


@pytest.mark.skipif(
    os.getenv("LLM_PROVIDER") != "bedrock",
    reason="Set LLM_PROVIDER=bedrock to run parity test",
)
def test_bedrock_provider_instantiates():
    settings = Settings(llm_provider="bedrock")
    provider = BedrockProvider(settings)
    assert provider.client is not None
