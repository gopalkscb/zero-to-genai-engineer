"""Supervisor exit gate and finding carry-forward tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.graph.nodes.reviewers import is_unfalsifiable, normalize_reviewer_findings
from app.graph.nodes.rewrite import format_findings_for_rewrite, rewrite_node
from app.graph.nodes.supervisor import (
    draft_is_static,
    merge_findings,
    route_after_supervisor,
    sort_findings_by_severity,
    supervisor_node,
)
from app.graph.state import Finding, ReviewerRole, Severity
from app.graph.trace import make_snapshot


def _finding(
    sev: Severity,
    problem: str = "issue",
    finding_id: str = "f1",
    reviewer: ReviewerRole = ReviewerRole.STYLE,
    resolved: bool = False,
    review_iteration: int = 0,
) -> Finding:
    return Finding(
        finding_id=finding_id,
        reviewer=reviewer,
        severity=sev,
        problem=problem,
        suggested_fix="fix it",
        resolved=resolved,
        review_iteration=review_iteration,
    )


class TestSupervisorExitGate:
    def test_empty_findings_exits(self):
        result = supervisor_node({"iteration": 0, "open_findings": [], "new_findings": []})
        assert result["converged"] is True
        assert route_after_supervisor({**result}) == "editor_score"

    def test_open_findings_routes_to_rewrite(self):
        result = supervisor_node(
            {
                "iteration": 1,
                "open_findings": [],
                "new_findings": [_finding(Severity.MAJOR, review_iteration=1)],
            }
        )
        assert result["converged"] is False
        assert route_after_supervisor(result) == "rewrite"

    def test_cap_hit_exits_with_flag(self):
        state = {
            "converged": False,
            "cap_hit_with_open_findings": True,
            "iteration": 5,
        }
        assert route_after_supervisor(state) == "editor_score"

    def test_does_not_remerge_processed_ids(self):
        first = _finding(Severity.MAJOR, "same issue", review_iteration=2)
        result = supervisor_node(
            {
                "iteration": 2,
                "open_findings": [],
                "new_findings": [first, first],
                "processed_finding_ids": [first.finding_id],
            }
        )
        assert result["open_findings"] == []
        assert result["converged"] is True

    def test_severity_ordering(self):
        findings = [
            _finding(Severity.MINOR, "c"),
            _finding(Severity.CRITICAL, "a"),
            _finding(Severity.MAJOR, "b"),
        ]
        ordered = sort_findings_by_severity(findings)
        assert ordered[0].severity == Severity.CRITICAL
        assert ordered[-1].severity == Severity.MINOR


class TestSeverityGate:
    def test_minor_findings_still_send_the_draft_back(self):
        result = supervisor_node(
            {
                "iteration": 3,
                "open_findings": [],
                "new_findings": [
                    _finding(Severity.MINOR, "The second image has no alt text", finding_id="m1", review_iteration=3)
                ],
            }
        )
        assert result["converged"] is False
        assert route_after_supervisor(result) == "rewrite"
        assert [item.finding_id for item in result["open_findings"]] == ["m1"]

    def test_major_finding_still_sends_the_draft_back(self):
        result = supervisor_node(
            {
                "iteration": 3,
                "open_findings": [],
                "new_findings": [
                    _finding(Severity.MAJOR, "unsupported claim", finding_id="j1", review_iteration=3)
                ],
            }
        )
        assert result["converged"] is False
        assert route_after_supervisor(result) == "rewrite"


class TestStallDetection:
    FROZEN = "# Title\n\nAn identical body paragraph that the rewrite never changes."

    def _frozen_history(self):
        return [
            make_snapshot(iteration=1, phase="rewrite", markdown=self.FROZEN),
            make_snapshot(iteration=2, phase="rewrite", markdown=self.FROZEN),
        ]

    def test_identical_rewrites_are_static(self):
        assert draft_is_static(self._frozen_history()) is True

    def test_a_real_rewrite_is_not_static(self):
        history = [
            make_snapshot(iteration=1, phase="rewrite", markdown="# Title\n\nShort body."),
            make_snapshot(
                iteration=2,
                phase="rewrite",
                markdown="# Title\n\nA completely rewritten body that adds a worked example and two citations.",
            ),
        ]
        assert draft_is_static(history) is False

    def test_single_rewrite_cannot_be_static(self):
        assert draft_is_static([make_snapshot(iteration=1, phase="rewrite", markdown=self.FROZEN)]) is False

    def test_loop_exits_when_nothing_resolves_and_the_draft_freezes(self):
        result = supervisor_node(
            {
                "iteration": 2,
                "open_findings": [_finding(Severity.MAJOR, "unsupported claim", finding_id="s1")],
                "new_findings": [],
                "iteration_history": self._frozen_history(),
                "stall_count": 1,
            }
        )
        assert result["stalled"] is True
        assert route_after_supervisor(result) == "editor_score"
        assert [item.finding_id for item in result["accepted_findings"]] == ["s1"]

    def test_one_static_pass_is_not_enough_to_quit(self):
        result = supervisor_node(
            {
                "iteration": 2,
                "open_findings": [_finding(Severity.MAJOR, "unsupported claim", finding_id="s1")],
                "new_findings": [],
                "iteration_history": self._frozen_history(),
                "stall_count": 0,
            }
        )
        assert result["stall_count"] == 1
        assert result["stalled"] is False
        assert route_after_supervisor(result) == "rewrite"

    def test_progress_resets_the_stall_counter(self):
        previous = [
            _finding(Severity.MAJOR, "unsupported claim", finding_id="s1"),
            _finding(Severity.MAJOR, "wrong version number", finding_id="s2"),
        ]
        fixed = _finding(
            Severity.MAJOR, "unsupported claim", finding_id="s1", resolved=True, review_iteration=2
        )
        result = supervisor_node(
            {
                "iteration": 2,
                "open_findings": previous,
                "new_findings": [fixed],
                "iteration_history": self._frozen_history(),
                "stall_count": 1,
            }
        )
        assert result["stall_count"] == 0
        assert result["stalled"] is False
        assert route_after_supervisor(result) == "rewrite"


class TestFindingCarryForward:
    def test_unmentioned_previous_finding_stays_open(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        open_findings, resolved, _, resolved_count, new_count = merge_findings(
            previous, incoming=[], resolved=[], processed_ids=set()
        )
        assert [item.finding_id for item in open_findings] == ["abc"]
        assert resolved_count == 0
        assert new_count == 0
        assert resolved == []

    def test_explicit_resolved_closes_finding(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        incoming = [_finding(Severity.MAJOR, "missing citation", finding_id="abc", resolved=True)]
        open_findings, resolved, _, resolved_count, new_count = merge_findings(
            previous, incoming, resolved=[], processed_ids=set()
        )
        assert open_findings == []
        assert resolved_count == 1
        assert resolved[0].finding_id == "abc"
        assert resolved[0].resolved is True
        assert new_count == 0

    def test_same_fingerprint_does_not_duplicate(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        incoming = [_finding(Severity.MAJOR, "missing citation", finding_id="zzz")]
        open_findings, _, _, _, new_count = merge_findings(
            previous, incoming, resolved=[], processed_ids=set()
        )
        assert len(open_findings) == 1
        assert open_findings[0].finding_id == "abc"
        assert new_count == 0

    def test_new_distinct_finding_is_added(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        incoming = [_finding(Severity.MINOR, "awkward heading", finding_id="def")]
        open_findings, _, processed, _, new_count = merge_findings(
            previous, incoming, resolved=[], processed_ids=set()
        )
        assert {item.finding_id for item in open_findings} == {"abc", "def"}
        assert new_count == 1
        assert "def" in processed

    def test_supervisor_ignores_stale_new_findings_from_prior_iteration(self):
        stale = _finding(Severity.MAJOR, "old wording", finding_id="old", review_iteration=0)
        previous = [_finding(Severity.MAJOR, "old wording", finding_id="old")]
        resolved_this_pass = _finding(
            Severity.MAJOR, "old wording", finding_id="old", resolved=True, review_iteration=1
        )
        result = supervisor_node(
            {
                "iteration": 1,
                "open_findings": previous,
                "new_findings": [stale, resolved_this_pass],
            }
        )
        assert result["converged"] is True
        assert result["open_findings"] == []
        assert result["resolved_findings"][0].finding_id == "old"


class TestRewriteUsesAllFindings:
    def test_format_includes_every_finding_id(self):
        findings = [
            _finding(Severity.CRITICAL, "wrong fact", finding_id="c1", reviewer=ReviewerRole.TECHNICAL),
            _finding(Severity.MINOR, "long sentence", finding_id="m1"),
        ]
        text = format_findings_for_rewrite(findings)
        assert "ID c1" in text
        assert "ID m1" in text
        assert "wrong fact" in text

    def test_rewrite_keeps_open_findings_for_next_review(self):
        findings = [
            _finding(Severity.MAJOR, "missing citation", finding_id="abc"),
            _finding(Severity.MINOR, "awkward heading", finding_id="def"),
        ]
        mock_llm = MagicMock()
        mock_llm.complete.return_value = "# Revised draft"
        with patch("app.graph.nodes.rewrite.LLMClient", return_value=mock_llm):
            result = rewrite_node(
                {
                    "draft_markdown": "# Old draft",
                    "open_findings": findings,
                    "iteration": 0,
                }
            )
        assert result["iteration"] == 1
        assert [item.finding_id for item in result["open_findings"]] == ["abc", "def"]
        prompt = mock_llm.complete.call_args.args[1][1]["content"]
        assert "ID abc" in prompt
        assert "ID def" in prompt
        assert "missing citation" in prompt


class TestReviewerIdReuse:
    def test_reuses_previous_id_and_can_mark_resolved(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        raw = [
            {
                "finding_id": "abc",
                "severity": "major",
                "problem": "missing citation",
                "suggested_fix": "add it",
                "resolved": True,
            }
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous, iteration=2
        )
        assert len(findings) == 1
        assert findings[0].finding_id == "abc"
        assert findings[0].resolved is True
        assert findings[0].review_iteration == 2

    def test_caps_new_findings(self):
        raw = [
            {"severity": "minor", "problem": f"nit {idx}", "suggested_fix": "tweak"}
            for idx in range(5)
        ]
        findings, logs = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous=[], iteration=0, max_new=2
        )
        assert len(findings) == 2
        assert any("Dropped extra" in item.message for item in logs)

    def test_discovery_closes_so_late_passes_only_verify(self):
        """Without this the loop adds work every pass and can never converge."""
        raw = [
            {"severity": "minor", "problem": f"brand new nit {idx}", "suggested_fix": "tweak"}
            for idx in range(3)
        ]
        findings, logs = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous=[], iteration=7, max_new=0
        )
        assert findings == []
        assert all("discovery closed" in item.message for item in logs)

    def test_verify_pass_still_resolves_previous_findings(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        raw = [
            {"finding_id": "abc", "severity": "major", "problem": "missing citation", "resolved": True},
            {"severity": "minor", "problem": "unrelated nit", "suggested_fix": "tweak"},
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous, iteration=7, max_new=0
        )
        assert [item.finding_id for item in findings] == ["abc"]
        assert findings[0].resolved is True

    def test_rejects_unfalsifiable_new_finding(self):
        """A taste opinion has no fixed state, so it would be re-reported forever."""
        raw = [
            {
                "severity": "minor",
                "problem": "The conclusion could be more impactful",
                "suggested_fix": "punch it up",
            }
        ]
        findings, logs = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous=[], iteration=0, max_new=2
        )
        assert findings == []
        assert any("unfalsifiable" in item.message for item in logs)

    def test_keeps_concrete_new_finding(self):
        raw = [
            {
                "severity": "minor",
                "problem": "The second image has no alt text",
                "suggested_fix": "add alt text",
            }
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous=[], iteration=0, max_new=2
        )
        assert len(findings) == 1
        assert findings[0].problem == "The second image has no alt text"

    def test_unfalsifiable_finding_does_not_consume_a_new_slot(self):
        raw = [
            {"severity": "minor", "problem": "The intro could benefit from energy", "suggested_fix": "x"},
            {
                "severity": "major",
                "problem": "The draft says BPE merges 50k pairs but the source says 32k",
                "suggested_fix": "correct the number",
            },
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.TECHNICAL, raw, previous=[], iteration=0, max_new=1
        )
        assert len(findings) == 1
        assert findings[0].severity == Severity.MAJOR

    def test_vague_filter_never_blocks_a_resolution(self):
        previous = [_finding(Severity.MINOR, "The intro could be more engaging", finding_id="old1")]
        raw = [
            {
                "finding_id": "old1",
                "severity": "minor",
                "problem": "The intro could be more engaging",
                "resolved": True,
            }
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous, iteration=3, max_new=0
        )
        assert [item.finding_id for item in findings] == ["old1"]
        assert findings[0].resolved is True

    def test_real_defects_are_not_mistaken_for_hedging(self):
        assert is_unfalsifiable("The parse_tokens example crashes when text is empty") is False
        assert is_unfalsifiable("The parse_tokens example could crash on empty input") is False
        assert is_unfalsifiable("The transition between sections could be smoother") is True
        assert is_unfalsifiable("") is True

    def test_a_hedge_survives_when_the_finding_points_at_something_checkable(self):
        """Soft wording around a quote or an absence is still a closeable defect."""
        quoted = "The claim 'BPE never produces unknown tokens' could be misread as absolute"
        absent = "The article lacks a clear definition of BPE in the introduction"
        numeric = "The draft says the vocabulary could be 50257 but the source says 32000"
        assert is_unfalsifiable(quoted) is False
        assert is_unfalsifiable(absent) is False
        assert is_unfalsifiable(numeric) is False
        # Nothing to point at, so there is no version of the draft that closes it.
        assert is_unfalsifiable("The conclusion could benefit from a stronger call to action") is True

    def test_matches_previous_by_problem_when_id_is_missing(self):
        previous = [_finding(Severity.MAJOR, "missing citation", finding_id="abc")]
        raw = [
            {
                "finding_id": "",
                "severity": "major",
                "problem": "missing citation",
                "suggested_fix": "add it",
                "resolved": False,
            }
        ]
        findings, _ = normalize_reviewer_findings(
            ReviewerRole.STYLE, raw, previous, iteration=1
        )
        assert findings[0].finding_id == "abc"
        assert findings[0].resolved is False
