"""Supervisor — merge findings, carry unresolved ones forward, exit gate."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.config import get_settings
from app.graph.state import AgentState, Finding, LogEntry, LogLevel, Severity
from app.graph.trace import make_snapshot

# Every still-open finding holds the loop. Shipping with eight "minor" leftovers is how
# a draft reaches the human gate with no definition, no worked example, and no citations.
BLOCKING_SEVERITIES = (Severity.CRITICAL, Severity.MAJOR, Severity.MINOR)

# Consecutive review passes that may resolve nothing while the draft stands still before
# the loop gives up. Two is enough to tell a slow fix apart from a stuck rewrite.
STALL_LIMIT = 2

# Rewrites always jitter the wording a little, so demand near-identity rather than equality.
_STATIC_DRAFT_RATIO = 0.98


def _severity_rank(sev: Severity) -> int:
    return {Severity.CRITICAL: 0, Severity.MAJOR: 1, Severity.MINOR: 2}[sev]


def blocking_findings(findings: list[Finding]) -> list[Finding]:
    return [
        item
        for item in findings
        if not getattr(item, "resolved", False) and item.severity in BLOCKING_SEVERITIES
    ]


def _snapshot_field(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


def draft_is_static(history: list[Any] | None) -> bool:
    """True when the last two rewrites produced effectively the same draft."""
    drafts = [
        text
        for item in history or []
        if _snapshot_field(item, "phase") == "rewrite"
        and (text := re.sub(r"\s+", " ", str(_snapshot_field(item, "markdown") or "")).strip())
    ]
    if len(drafts) < 2:
        return False
    previous, current = drafts[-2], drafts[-1]
    if previous == current:
        return True
    return SequenceMatcher(None, previous, current).ratio() >= _STATIC_DRAFT_RATIO


def finding_fingerprint(finding: Finding) -> str:
    role = finding.reviewer.value if hasattr(finding.reviewer, "value") else str(finding.reviewer)
    problem = re.sub(r"\s+", " ", (finding.problem or "").strip().lower())[:100]
    return f"{role}:{problem}"


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[str] = set()
    unique: list[Finding] = []
    for item in findings:
        key = finding_fingerprint(item)
        if key in seen or item.finding_id in {u.finding_id for u in unique}:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def merge_findings(
    previous_open: list[Finding],
    incoming: list[Finding],
    resolved: list[Finding],
    processed_ids: set[str],
) -> tuple[list[Finding], list[Finding], set[str], int, int]:
    """Keep previous findings open until a reviewer marks the same ID/fingerprint resolved.

    New findings are added only when they are a distinct problem.
    """
    prev_by_id = {item.finding_id: item for item in previous_open}
    prev_by_fp = {finding_fingerprint(item): item for item in previous_open}
    resolved_fps = {finding_fingerprint(item) for item in resolved}

    latest_by_key: dict[str, Finding] = {}
    for item in incoming:
        key = item.finding_id or finding_fingerprint(item)
        latest_by_key[key] = item
    latest_incoming = list(latest_by_key.values())

    matched_ids: set[str] = set()
    still_open: list[Finding] = []
    newly_resolved: list[Finding] = []

    for item in latest_incoming:
        fp = finding_fingerprint(item)
        prev = prev_by_id.get(item.finding_id) or prev_by_fp.get(fp)
        if prev is None:
            continue
        matched_ids.add(prev.finding_id)
        if item.resolved:
            newly_resolved.append(prev.model_copy(update={"resolved": True}))
        else:
            still_open.append(
                prev.model_copy(
                    update={
                        "resolved": False,
                        "problem": item.problem or prev.problem,
                        "suggested_fix": item.suggested_fix or prev.suggested_fix,
                    }
                )
            )

    # Cautious default: if a reviewer did not mention a previous finding, keep it open.
    for prev in previous_open:
        if prev.finding_id in matched_ids:
            continue
        still_open.append(prev)

    new_count = 0
    for item in latest_incoming:
        if item.resolved:
            continue
        if item.finding_id in prev_by_id or finding_fingerprint(item) in prev_by_fp:
            continue
        fp = finding_fingerprint(item)
        if fp in resolved_fps:
            continue
        if item.finding_id in processed_ids:
            continue
        still_open.append(item)
        processed_ids.add(item.finding_id)
        new_count += 1

    open_findings = [item for item in _dedupe_findings(still_open) if not item.resolved]
    resolved_out = _dedupe_findings(list(resolved) + newly_resolved)
    return open_findings, resolved_out, processed_ids, len(newly_resolved), new_count


def supervisor_node(state: AgentState) -> dict:
    settings = get_settings()
    iteration = state.get("iteration", 0)
    previous_open = [item for item in state.get("open_findings", []) if not getattr(item, "resolved", False)]
    # new_findings is append-only across the whole run. Only this review pass is a verdict.
    incoming = [
        item
        for item in (state.get("new_findings", []) or [])
        if getattr(item, "review_iteration", 0) == iteration
    ]
    resolved = list(state.get("resolved_findings", []))
    processed = set(state.get("processed_finding_ids", []))

    open_findings, resolved, processed, resolved_count, new_count = merge_findings(
        previous_open, incoming, resolved, processed
    )

    blocking = blocking_findings(open_findings)
    converged = len(blocking) == 0

    # A pass that resolves nothing and leaves the draft untouched will keep doing that.
    stall_count = state.get("stall_count", 0) or 0
    if not converged and resolved_count == 0 and new_count == 0 and draft_is_static(state.get("iteration_history")):
        stall_count += 1
    else:
        stall_count = 0
    stalled = stall_count >= STALL_LIMIT and not converged

    cap_hit = iteration >= settings.max_review_iterations and not converged
    exit_with_open = cap_hit or stalled

    logs: list[LogEntry] = [
        LogEntry(
            node="supervisor",
            level=LogLevel.INFO,
            message=(
                f"Iteration {iteration}: {len(open_findings)} open finding(s), "
                f"{len(blocking)} blocking "
                f"(resolved {resolved_count}, new {new_count}, carried {len(previous_open)})"
            ),
            iteration=iteration,
        )
    ]

    accepted = list(state.get("accepted_findings", []) or [])
    if stalled:
        accepted = open_findings
        logs.append(
            LogEntry(
                node="supervisor",
                level=LogLevel.WARNING,
                message=(
                    f"Stalled: {STALL_LIMIT} passes resolved nothing and the rewrite stopped "
                    f"changing the draft. Exiting with {len(open_findings)} finding(s) accepted"
                ),
                iteration=iteration,
            )
        )
    elif cap_hit:
        accepted = open_findings
        logs.append(
            LogEntry(
                node="supervisor",
                level=LogLevel.WARNING,
                message=(
                    f"Max review iterations ({settings.max_review_iterations}) reached "
                    f"with {len(open_findings)} open findings kept as accepted findings"
                ),
                iteration=iteration,
            )
        )

    if stalled:
        summary = f"Stalled, {len(open_findings)} findings accepted"
    elif cap_hit:
        summary = f"Cap reached, {len(open_findings)} findings accepted"
    else:
        summary = (
            f"{len(open_findings)} open ({len(blocking)} blocking), "
            f"{resolved_count} resolved, {new_count} new"
        )

    markdown = state.get("draft_markdown") or state.get("final_markdown") or ""
    snapshot = make_snapshot(
        iteration=iteration,
        phase="cap" if exit_with_open else "review",
        markdown=markdown,
        findings=open_findings,
        summary=summary,
    )

    return {
        "open_findings": open_findings,
        "resolved_findings": resolved,
        "accepted_findings": accepted,
        "processed_finding_ids": list(processed),
        "converged": converged,
        "cap_hit_with_open_findings": cap_hit,
        "stalled": stalled,
        "stall_count": stall_count,
        "iteration_history": [snapshot],
        "logs": logs,
        "editor_loop": False,
    }


def route_after_supervisor(state: AgentState) -> str:
    if (
        state.get("converged")
        or state.get("cap_hit_with_open_findings")
        or state.get("stalled")
    ):
        return "editor_score"
    return "rewrite"


def sort_findings_by_severity(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: _severity_rank(f.severity))
