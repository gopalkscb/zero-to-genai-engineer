"""LangSmith tracing helpers."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

from app.config import get_settings


def configure_tracing():
    settings = get_settings()
    if settings.tracing_enabled and settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"


@contextmanager
def trace_run(run_id: str, node: str, metadata: dict[str, Any] | None = None) -> Generator[str, None, None]:
    """Yield trace_url placeholder; real URL populated when LangSmith enabled."""
    configure_tracing()
    trace_url = ""
    if get_settings().tracing_enabled:
        trace_url = f"https://smith.langchain.com/o/default/projects/p/{get_settings().langsmith_project}?run_id={run_id}&node={node}"
    yield trace_url
