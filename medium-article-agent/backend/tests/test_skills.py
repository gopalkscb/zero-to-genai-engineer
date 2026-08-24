"""House skill (backend/skills/medium.md) is loaded, compacted, and enforced."""

from __future__ import annotations

from app.config import get_settings
from app.editorial.skills import apply_deterministic_fixes, compact_skills, extract_banned_phrases, lint_article
from app.graph.nodes.skills_lint import skills_lint_node
from app.graph.state import ReviewerRole


def test_style_guide_file_is_loaded():
    guide = get_settings().load_style_guide()
    assert "Banned Phrases" in guide
    assert "AI disclosure" in guide or "AI assistance" in guide
    compact = compact_skills(guide)
    assert "Banned Phrases" in compact
    assert "Pre-Publish Checklist" in compact
    banned = extract_banned_phrases(guide)
    assert "delve" in banned
    assert "in conclusion" in banned


def test_lint_catches_banned_phrase_and_missing_disclosure():
    draft = """# In today's fast-paced world of agents

Let us delve into LangGraph and leverage the pipeline.

## A heading

This is still too short.
"""
    guide = get_settings().load_style_guide()
    audit = lint_article(draft, skills_rules=guide)
    failed = {item.check_id: item for item in audit.checks if not item.passed}
    assert "banned" in failed
    assert "disclosure" in failed
    assert "wordcount" in failed


def test_skills_lint_node_uses_stable_ids():
    result = skills_lint_node(
        {
            "draft_markdown": "# Title\n\nLet us delve into this.\n",
            "skills_rules": get_settings().load_style_guide(),
            "iteration": 0,
            "open_findings": [],
        }
    )
    ids = {item.finding_id for item in result["new_findings"] if not item.resolved}
    assert "skills-banned" in ids
    assert "skills-disclosure" in ids
    assert all(item.reviewer == ReviewerRole.SKILLS for item in result["new_findings"])
    assert result["skills_audit"]["failed"] >= 1


def test_deterministic_fixes_add_disclosure_and_strip_dashes():
    text = apply_deterministic_fixes("# Title\n\nA claim — with an em dash.\n")
    assert "AI assistance" in text
    assert "—" not in text
