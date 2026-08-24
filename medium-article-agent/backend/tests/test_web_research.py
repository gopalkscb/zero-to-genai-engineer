"""Web research node tests (no live DuckDuckGo)."""

from __future__ import annotations

from unittest.mock import patch

from app.graph.nodes.web_research import build_research_queries, web_research_node
from app.graph.state import ArticlePlan, PyramidSection, WebSnippet


def test_build_research_queries_caps_and_dedupes():
    plan = ArticlePlan(
        title="BPE Tokenization",
        thesis="BPE is the standard tokenizer for modern LLMs",
        pyramid_outline=[
            PyramidSection(level=1, title="How BPE works"),
            PyramidSection(level=2, title="Sampling"),
        ],
    )
    queries = build_research_queries(plan, "BPE Tokenization")
    assert len(queries) <= 4
    assert queries[0] == "BPE Tokenization"
    assert len(queries) == len(set(q.lower() for q in queries))


def test_web_research_skipped_when_disabled():
    result = web_research_node({"enable_web_research": False, "plan": None})
    assert result["web_research"].enabled is False
    assert result["web_research"].snippets == []
    assert "skipped" in result["logs"][0].message.lower()


def test_web_research_collects_snippets_when_enabled():
    plan = ArticlePlan(title="LangGraph", thesis="Stateful agents")
    fake = [
        WebSnippet(query="LangGraph", title="Docs", url="https://example.com", snippet="Graphs")
    ]
    with patch("app.graph.nodes.web_research._search_duckduckgo", return_value=fake):
        result = web_research_node(
            {"enable_web_research": True, "plan": plan, "topic_hint": "LangGraph"}
        )
    assert result["web_research"].enabled is True
    assert result["web_research"].snippets
    assert "snippet" in result["logs"][0].message.lower()
