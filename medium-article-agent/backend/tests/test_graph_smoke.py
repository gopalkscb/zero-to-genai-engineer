"""End-to-end graph smoke test with mocked LLM."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.graph.build_graph import build_graph
from app.graph.state import ArticlePlan, PipelineStatus, PyramidSection


MOCK_PLAN = ArticlePlan(
    title="Test Article",
    subtitle="A subtitle",
    audience="Developers",
    thesis="AI agents are useful",
    pyramid_outline=[
        PyramidSection(level=1, title="Intro", bullets=["Hook", "Problem"]),
        PyramidSection(level=2, title="Body", bullets=["Point A", "Point B"]),
    ],
    image_prompts=["A robot writing an article"],
    estimated_word_count=1200,
)

MOCK_DRAFT = "# Test Article\n\nThis is a clean draft without special dashes.\n\n## Intro\n\nContent here."


@pytest.fixture
def mock_llm():
    patches = [
        patch("app.graph.nodes.plan.LLMClient"),
        patch("app.graph.nodes.draft.LLMClient"),
        patch("app.graph.nodes.reviewers.LLMClient"),
        patch("app.graph.nodes.rewrite.LLMClient"),
        patch("app.graph.nodes.rewrite_voice.LLMClient"),
        patch("app.graph.nodes.editor_score.LLMClient"),
        patch("app.graph.nodes.headline.LLMClient"),
        patch("app.graph.nodes.style_pass.LLMClient"),
        patch("app.graph.nodes.final_rewrite.LLMClient"),
        patch("app.graph.nodes.grounding_recheck.LLMClient"),
    ]
    mocks = [p.start() for p in patches]
    instance = MagicMock()

    def complete_side_effect(stage, messages, structured_schema=None, temperature=0.7):
        if structured_schema and structured_schema.__name__ == "ArticlePlan":
            return MOCK_PLAN
        if structured_schema:
            name = structured_schema.__name__
            if name == "ReviewerOutput":
                return structured_schema.model_validate({"findings": []})
            if name == "GroundingResult":
                return structured_schema.model_validate({"drift_detected": False, "issues": []})
            if name == "EditorScore":
                return structured_schema.model_validate(
                    {"score": 9, "notes": "Ready to ship", "ready": True, "defects": []}
                )
            if name == "HeadlineOutput":
                return structured_schema.model_validate(
                    {"title": "Test Article", "subtitle": "A subtitle", "dek": "A one-sentence dek."}
                )
            return structured_schema.model_validate({})
        return MOCK_DRAFT

    instance.complete.side_effect = complete_side_effect
    for mock_cls in mocks:
        mock_cls.return_value = instance
    skills = patch(
        "app.graph.build_graph.skills_lint_node",
        return_value={"new_findings": [], "skills_audit": {"checks": [], "passed": 0, "failed": 0}, "logs": []},
    )
    skills.start()
    yield instance
    skills.stop()
    for p in patches:
        p.stop()


@pytest.fixture
def mock_image():
    with (
        patch("app.graph.nodes.image_gen.ImageClient") as gen_cls,
        patch("app.graph.nodes.image_review.ImageClient") as review_cls,
    ):
        instance = MagicMock()
        instance.generate.return_value = b"\x89PNG\r\n\x1a\n"
        instance.save.return_value = "/tmp/test.png"
        instance.review.return_value = {"pass": True, "notes": "Clear figure", "retry_prompt": ""}
        gen_cls.return_value = instance
        review_cls.return_value = instance
        yield instance


def test_linear_graph_ingests_multiple_files(mock_llm, mock_image):
    graph = build_graph(linear_only=True)
    result = graph.invoke(
        {
            "run_id": "multi-linear",
            "uploaded_files": [
                {
                    "content": b"Speaker A: Byte Pair Encoding starts from characters.",
                    "filename": "session.transcript",
                    "source_id": "tx1",
                },
                {
                    "content": b"Token count is billed. GPT-2 used 50257 tokens.",
                    "filename": "billing-notes.md",
                    "source_id": "tx2",
                },
            ],
            "topic_hint": "BPE and cost",
        }
    )
    names = [doc.filename for doc in result.get("documents") or []]
    assert names == ["session.transcript", "billing-notes.md"]
    combined = result.get("combined_text") or ""
    assert "session.transcript" in combined
    assert "billing-notes.md" in combined
    assert result.get("plan") is not None
    assert result.get("draft_markdown")


def test_ingest_to_plan_linear(mock_llm, mock_image):
    graph = build_graph(linear_only=True)
    result = graph.invoke(
        {
            "run_id": "test-run",
            "uploaded_files": [
                {
                    "content": b"Speaker A: Hello world.\n\nSpeaker B: Testing agents.",
                    "filename": "session.transcript",
                    "source_id": "tx1",
                }
            ],
            "topic_hint": "AI agents",
        }
    )
    assert result.get("plan") is not None
    assert result.get("draft_markdown")
    assert "skills_rules" in result or result.get("documents")


def test_full_graph_reaches_interrupt(mock_llm, mock_image):
    graph = build_graph()
    config = {"configurable": {"thread_id": "smoke-test"}}
    result = graph.invoke(
        {
            "run_id": "smoke-test",
            "uploaded_files": [
                {
                    "content": b"# Sample\n\nSome source content for grounding.",
                    "filename": "notes.md",
                    "source_id": "t1",
                }
            ],
            "topic_hint": "Testing",
        },
        config=config,
    )
    # Graph should pause at human_gate interrupt
    assert result is not None
