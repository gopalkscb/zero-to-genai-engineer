"""Architecture tests for the editorial graph: image loop, voice rewrite, editor gate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.graph.build_graph import (
    REVIEWERS,
    fan_out_reviewers,
    route_after_image_review,
    route_after_rewrite_voice,
)
from app.graph.nodes.editor_score import EditorScore, editor_score_node, route_after_editor_score
from app.graph.nodes.headline import apply_headline, headline_node
from app.graph.nodes.image_gen import image_gen_node
from app.graph.nodes.image_review import image_review_node, images_need_redraw
from app.graph.nodes.rewrite_voice import rewrite_voice_node
from app.graph.state import ArticlePlan, Finding, ImageAsset, ImageStatus, ReviewerRole, Severity


def test_six_specialist_reviewers_fan_out():
    sends = fan_out_reviewers({})
    assert [item.node for item in sends] == list(REVIEWERS)
    assert "reviewer_reader" in REVIEWERS
    assert "reviewer_skills" in REVIEWERS
    assert len(sends) == 6


def test_image_gen_does_not_review_or_redraw():
    mock_client = MagicMock()
    mock_client.generate.return_value = b"\x89PNG\r\n\x1a\n"
    mock_client.save.return_value = "/tmp/test.png"
    plan = ArticlePlan(title="BPE", thesis="pairs merge", image_prompts=["tiles merging"])
    with patch("app.graph.nodes.image_gen.ImageClient", return_value=mock_client):
        result = image_gen_node(
            {
                "run_id": "img-gen-only",
                "plan": plan,
                "draft_markdown": "# BPE\n\n## How it works\n\nBody\n",
            }
        )
    mock_client.review.assert_not_called()
    generated = [img for img in result["images"] if img.status == ImageStatus.GENERATED]
    assert generated
    assert all(img.review_passed is False for img in generated)
    assert all("Awaiting" in img.review_notes for img in generated)


def test_missing_image_file_does_not_request_redraw(tmp_path: Path):
    images = [
        ImageAsset(
            image_id="img_1",
            prompt="tiles",
            caption="Cover",
            local_path=str(tmp_path / "missing.png"),
            status=ImageStatus.GENERATED,
            review_passed=False,
            review_notes="Awaiting art-direction review.",
        )
    ]
    mock_client = MagicMock()
    with patch("app.graph.nodes.image_review.ImageClient", return_value=mock_client):
        result = image_review_node({"images": images, "run_id": "x"})
    mock_client.review.assert_not_called()
    assert result["images"][0].review_passed is True
    assert images_need_redraw(result) is False


def test_failed_art_direction_routes_to_redraw():
    images = [
        ImageAsset(
            image_id="img_1",
            prompt="blob",
            status=ImageStatus.GENERATED,
            review_passed=False,
            review_notes="Abstract mush",
            redraw_prompt="Tiles merging into larger tiles, no text",
        )
    ]
    nxt = route_after_image_review({"images": images, "image_redraw_count": 0})
    assert nxt == "image_redraw"
    cap = route_after_image_review({"images": images, "image_redraw_count": 2})
    assert [item.node for item in cap] == list(REVIEWERS)


def test_rewrite_voice_does_not_bump_iteration():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = "# Voice pass\n\nStill 1400 words of substance."
    findings = [
        Finding(
            finding_id="abc",
            reviewer=ReviewerRole.TECHNICAL,
            severity=Severity.MAJOR,
            problem="The draft never defines BPE",
            suggested_fix="Define it in paragraph one",
        )
    ]
    with patch("app.graph.nodes.rewrite_voice.LLMClient", return_value=mock_llm):
        result = rewrite_voice_node(
            {"draft_markdown": "# Old", "open_findings": findings, "iteration": 2}
        )
    assert "iteration" not in result
    assert [item.finding_id for item in result["open_findings"]] == ["abc"]
    assert result["iteration_history"][0].phase == "voice"


def test_editor_loop_skips_specialists():
    nxt = route_after_rewrite_voice({"editor_loop": True})
    assert nxt == "editor_score"
    sends = route_after_rewrite_voice({"editor_loop": False})
    assert [item.node for item in sends] == list(REVIEWERS)


def test_editor_score_below_bar_injects_findings_and_rewrites():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = EditorScore(
        score=5.0,
        notes="No worked example.",
        ready=False,
        defects=[{"problem": "The draft never walks a merge with numbers", "suggested_fix": "Add one", "severity": "major"}],
    )
    with patch("app.graph.nodes.editor_score.LLMClient", return_value=mock_llm):
        result = editor_score_node(
            {
                "draft_markdown": "# Thin outline",
                "iteration": 1,
                "open_findings": [],
                "editor_retries": 0,
            }
        )
    assert result["editor_loop"] is True
    assert result["editor_retries"] == 1
    assert result["open_findings"][0].reviewer == ReviewerRole.EDITOR
    assert route_after_editor_score(result) == "rewrite"


def test_editor_score_at_bar_ships_to_headline():
    mock_llm = MagicMock()
    mock_llm.complete.return_value = EditorScore(score=8.5, notes="Publishable.", ready=True, defects=[])
    with patch("app.graph.nodes.editor_score.LLMClient", return_value=mock_llm):
        result = editor_score_node(
            {
                "draft_markdown": "# Solid",
                "iteration": 2,
                "open_findings": [],
                "editor_retries": 0,
            }
        )
    assert result["editor_loop"] is False
    assert route_after_editor_score(result) == "headline"


def test_stalled_review_does_not_reopen_editor_loop():
    assert (
        route_after_editor_score({"editor_score": 4.0, "editor_retries": 0, "stalled": True})
        == "headline"
    )


def test_headline_rewrites_h1_and_inserts_dek():
    out = apply_headline("# Old title\n\nBody starts here.\n", "New title", "A subtitle", "One sentence dek.")
    assert out.startswith("# New title")
    assert "*A subtitle*" in out
    assert "One sentence dek." in out
    from app.graph.nodes.headline import HeadlineOutput

    mock_llm = MagicMock()
    mock_llm.complete.return_value = HeadlineOutput(
        title="New title", subtitle="A subtitle", dek="One sentence dek."
    )
    with patch("app.graph.nodes.headline.LLMClient", return_value=mock_llm):
        result = headline_node(
            {
                "draft_markdown": "# Old title\n\nBody starts here.\n",
                "plan": ArticlePlan(title="Old title", subtitle=""),
            }
        )
    assert result["plan"].title == "New title"
    assert "# New title" in result["draft_markdown"]


def test_compiled_graph_contains_new_editorial_nodes():
    from app.graph.build_graph import build_graph

    graph = build_graph()
    names = set(graph.get_graph().nodes)
    assert {
        "image_review",
        "image_redraw",
        "rewrite_voice",
        "editor_score",
        "headline",
        "reviewer_reader",
        "reviewer_skills",
    } <= names
    assert "quiz_gen" not in names
