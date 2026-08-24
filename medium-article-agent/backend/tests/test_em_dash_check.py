"""Em/en dash deterministic check tests."""

from __future__ import annotations

from app.utils.dash_check import assert_no_em_en_dash, find_em_en_dash_violations, strip_em_en_dashes


class TestEmDashCheck:
    def test_clean_text_passes(self):
        text = "This is clean text with a hyphen-word and commas, periods."
        assert assert_no_em_en_dash(text) == []

    def test_em_dash_detected(self):
        text = "This has an em dash\u2014right here."
        violations = find_em_en_dash_violations(text)
        assert len(violations) == 1
        assert violations[0]["char"] == "em dash"

    def test_en_dash_detected(self):
        text = "Pages 1\u201310 are relevant."
        violations = find_em_en_dash_violations(text)
        assert len(violations) == 1
        assert violations[0]["char"] == "en dash"

    def test_strip_removes_violations(self):
        text = "Hello\u2014world and 1\u201310."
        cleaned = strip_em_en_dashes(text)
        assert assert_no_em_en_dash(cleaned) == []
