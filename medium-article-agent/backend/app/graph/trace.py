"""Demo trace: iteration history, node visits, LangGraph topology."""

from __future__ import annotations

import re
from typing import Any

from app.config import get_settings
from app.graph.state import (
    Finding,
    IterationSnapshot,
    LogEntry,
    NodeEvent,
    utc_now_iso,
)

GRAPH_PHASES = [
    {
        "id": "prepare",
        "label": "Prepare",
        "rows": [0, 1],
        "blurb": "Read sources, plan, write the first draft, generate figures, then art-direction review and redraw.",
    },
    {
        "id": "review",
        "label": "Review loop",
        "rows": [2, 3],
        "blurb": "Specialist reviewers plus house-skill lint, supervisor, substance + voice rewrite, then an editor score gate.",
    },
    {
        "id": "finish",
        "label": "Finish",
        "rows": [4],
        "blurb": "Headline, style polish, grounding check, your approval, export.",
    },
]

GRAPH_NODES = [
    {
        "id": "ingest",
        "label": "Ingest",
        "row": 0,
        "col": 0,
        "phase": "prepare",
        "does": "Parse uploads into blocks and load the Medium style guide.",
        "visit_means": "Times source files were parsed. This node runs once at the start.",
    },
    {
        "id": "plan",
        "label": "Plan",
        "row": 0,
        "col": 1,
        "phase": "prepare",
        "does": "Write the title, thesis, pyramid outline, and image prompts.",
        "visit_means": "Times an outline was written. Usually once.",
    },
    {
        "id": "web_research",
        "label": "Research",
        "row": 0,
        "col": 2,
        "phase": "prepare",
        "does": "Optional web snippets. Uploads stay the primary source.",
        "visit_means": "Times web research ran. Once if you enabled it, otherwise a no-op pass.",
    },
    {
        "id": "draft",
        "label": "Draft",
        "row": 0,
        "col": 3,
        "phase": "prepare",
        "does": "Write the first full Markdown article from the plan and sources.",
        "visit_means": "Times the first draft was written. Later edits happen in Rewrite, not here.",
    },
    {
        "id": "image_gen",
        "label": "Images",
        "row": 0,
        "col": 4,
        "phase": "prepare",
        "does": "Generate 2–5 illustrations and inject them into the draft.",
        "visit_means": "Times images were generated. Art-direction happens next, not inside this node.",
    },
    {
        "id": "image_review",
        "label": "Art review",
        "row": 1,
        "col": 4,
        "phase": "prepare",
        "does": "Vision-check each figure. Reject blobs, stock laptops, and illegible mush.",
        "visit_means": "Times art-direction ran. Goes up again after every redraw.",
    },
    {
        "id": "image_redraw",
        "label": "Redraw",
        "row": 1,
        "col": 5,
        "phase": "prepare",
        "does": "Regenerate only the figures that failed art-direction, then send them back to review.",
        "visit_means": "Times rejected figures were regenerated. Capped at two redraws.",
    },
    {
        "id": "reviewer_technical",
        "label": "Technical",
        "row": 2,
        "col": 0,
        "phase": "review",
        "does": "Check technical accuracy, then re-check the same findings after each rewrite.",
        "visit_means": "Review passes this specialist ran. Goes up by 1 after the first draft and after every rewrite.",
    },
    {
        "id": "reviewer_style",
        "label": "Style",
        "row": 2,
        "col": 1,
        "phase": "review",
        "does": "Check Medium voice, pacing, and house-style rules.",
        "visit_means": "Review passes this specialist ran. One pass per loop.",
    },
    {
        "id": "reviewer_structure",
        "label": "Structure",
        "row": 2,
        "col": 2,
        "phase": "review",
        "does": "Check flow, headings, and whether the pyramid outline still holds.",
        "visit_means": "Review passes this specialist ran. One pass per loop.",
    },
    {
        "id": "reviewer_grounding",
        "label": "Grounding",
        "row": 2,
        "col": 3,
        "phase": "review",
        "does": "Check claims against the uploaded source material.",
        "visit_means": "Review passes this specialist ran. One pass per loop.",
    },
    {
        "id": "reviewer_reader",
        "label": "Reader",
        "row": 2,
        "col": 4,
        "phase": "review",
        "does": "Read as a Medium subscriber: hook, definition before jargon, skimable H2s, usable takeaway.",
        "visit_means": "Review passes this specialist ran. One pass per loop.",
    },
    {
        "id": "reviewer_skills",
        "label": "House skill",
        "row": 2,
        "col": 5,
        "phase": "review",
        "does": "Deterministic lint of backend/skills/medium.md: banned phrases, disclosure, word count, H2s, golden sentences.",
        "visit_means": "Times the house-skill lint ran. One pass per loop. This is not an LLM guess.",
    },
    {
        "id": "supervisor",
        "label": "Supervisor",
        "row": 3,
        "col": 1,
        "phase": "review",
        "does": "Merge findings and keep unresolved IDs open. Any leftover finding sends the draft back.",
        "visit_means": "Times the exit gate scored the draft. Usually one more than Rewrite, because the first review happens before any rewrite.",
    },
    {
        "id": "rewrite",
        "label": "Rewrite",
        "row": 3,
        "col": 2,
        "phase": "review",
        "does": "Substance rewrite so every still-open finding is actually addressed.",
        "visit_means": "Review iterations performed. This is the number of times the agent tried to close the previous findings.",
    },
    {
        "id": "rewrite_voice",
        "label": "Voice",
        "row": 3,
        "col": 3,
        "phase": "review",
        "does": "Second rewrite agent. Polishes Medium voice without dropping facts or shrinking the piece.",
        "visit_means": "Times the voice pass ran. Fires after every substance rewrite.",
    },
    {
        "id": "editor_score",
        "label": "Editor",
        "row": 3,
        "col": 5,
        "phase": "review",
        "does": "Score the article 1–10. Below the publication bar, inject defects and rewrite again.",
        "visit_means": "Times the editor-in-chief scored the draft. Fires after specialists converge, stall, or hit the cap.",
    },
    {
        "id": "headline",
        "label": "Headline",
        "row": 4,
        "col": 0,
        "phase": "finish",
        "does": "Rewrite the title, subtitle, and dek so a skimmer stops.",
        "visit_means": "Times the headline pass ran. Usually once, after the editor ships.",
    },
    {
        "id": "style_pass",
        "label": "Style pass",
        "row": 4,
        "col": 1,
        "phase": "finish",
        "does": "Terminal polish for Medium voice. Strips em dashes and leftover draft artifacts.",
        "visit_means": "Times the finishing style pass ran. Fires after the headline.",
    },
    {
        "id": "final_rewrite",
        "label": "Final",
        "row": 4,
        "col": 2,
        "phase": "finish",
        "does": "Last structural cleanup before the grounding recheck.",
        "visit_means": "Times the final cleanup ran. Can run again if grounding still sees drift.",
    },
    {
        "id": "grounding_recheck",
        "label": "Ground check",
        "row": 4,
        "col": 3,
        "phase": "finish",
        "does": "Confirm the finished draft still matches the source material.",
        "visit_means": "Times the finished draft was checked against sources.",
    },
    {
        "id": "human_gate",
        "label": "Human gate",
        "row": 4,
        "col": 4,
        "phase": "finish",
        "does": "Pause for you to approve or send the draft back with notes.",
        "visit_means": "Times the pipeline paused for a human decision.",
    },
    {
        "id": "export",
        "label": "Export",
        "row": 4,
        "col": 5,
        "phase": "finish",
        "does": "Build clipboard Markdown and HTML for pasting into Medium.",
        "visit_means": "Times an export package was built. Fires after you approve.",
    },
]

GRAPH_EDGES = [
    {"from": "ingest", "to": "plan", "kind": "always", "label": "sources ready", "when": "Always, after files are parsed."},
    {"from": "plan", "to": "web_research", "kind": "always", "label": "outline ready", "when": "Always. Research may be a no-op if you left the web toggle off."},
    {"from": "web_research", "to": "draft", "kind": "always", "label": "write draft", "when": "Always. The first article is written here."},
    {"from": "draft", "to": "image_gen", "kind": "always", "label": "illustrate", "when": "Always. Images are generated from the plan prompts."},
    {"from": "image_gen", "to": "image_review", "kind": "always", "label": "art direction", "when": "Always. Every generated figure is vision-checked."},
    {"from": "image_review", "to": "image_redraw", "kind": "loop", "label": "rejected", "when": "If a figure fails art-direction and redraws remain under the cap of two."},
    {"from": "image_redraw", "to": "image_review", "kind": "loop", "label": "re-check", "when": "After every redraw. Only the new bytes are judged."},
    {"from": "image_review", "to": "reviewer_technical", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. All five reviewers run in parallel."},
    {"from": "image_review", "to": "reviewer_style", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. All five reviewers run in parallel."},
    {"from": "image_review", "to": "reviewer_structure", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. All five reviewers run in parallel."},
    {"from": "image_review", "to": "reviewer_grounding", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. All five reviewers run in parallel."},
    {"from": "image_review", "to": "reviewer_reader", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. All six reviewers run in parallel."},
    {"from": "image_review", "to": "reviewer_skills", "kind": "fanout", "label": "fan out", "when": "After figures pass or the redraw cap is hit. House-skill lint runs with the specialists."},
    {"from": "reviewer_technical", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Each reviewer sends its verdict to the supervisor."},
    {"from": "reviewer_style", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Each reviewer sends its verdict to the supervisor."},
    {"from": "reviewer_structure", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Each reviewer sends its verdict to the supervisor."},
    {"from": "reviewer_grounding", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Each reviewer sends its verdict to the supervisor."},
    {"from": "reviewer_reader", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Each reviewer sends its verdict to the supervisor."},
    {"from": "reviewer_skills", "to": "supervisor", "kind": "always", "label": "findings", "when": "Always. Failed house-skill checks become findings with stable IDs."},
    {"from": "supervisor", "to": "rewrite", "kind": "loop", "label": "findings remain", "when": "If any finding is still open and the loop has not hit the cap or stalled."},
    {"from": "rewrite", "to": "rewrite_voice", "kind": "always", "label": "polish voice", "when": "Always after a substance rewrite."},
    {"from": "rewrite_voice", "to": "reviewer_technical", "kind": "loop", "label": "re-review", "when": "After voice polish, specialists verdict the same finding IDs. Skip this when the editor sent the draft back."},
    {"from": "rewrite_voice", "to": "reviewer_style", "kind": "loop", "label": "re-review", "when": "After voice polish, specialists verdict the same finding IDs."},
    {"from": "rewrite_voice", "to": "reviewer_structure", "kind": "loop", "label": "re-review", "when": "After voice polish, specialists verdict the same finding IDs."},
    {"from": "rewrite_voice", "to": "reviewer_grounding", "kind": "loop", "label": "re-review", "when": "After voice polish, specialists verdict the same finding IDs."},
    {"from": "rewrite_voice", "to": "reviewer_reader", "kind": "loop", "label": "re-review", "when": "After voice polish, specialists verdict the same finding IDs."},
    {"from": "rewrite_voice", "to": "reviewer_skills", "kind": "loop", "label": "re-lint", "when": "After voice polish, house-skill lint re-checks the same IDs."},
    {"from": "rewrite_voice", "to": "editor_score", "kind": "loop", "label": "editor recheck", "when": "If the editor injected defects, skip the specialists and score again."},
    {"from": "supervisor", "to": "editor_score", "kind": "exit", "label": "clean, stalled, or cap", "when": "If no findings remain, or two passes resolved nothing, or the max review iterations were reached."},
    {"from": "editor_score", "to": "rewrite", "kind": "loop", "label": "below bar", "when": "If the editor score is under 8 and editor retries remain."},
    {"from": "editor_score", "to": "headline", "kind": "exit", "label": "publication bar", "when": "If the score is at least 8, or the editor retry cap was hit, or the review loop already stalled."},
    {"from": "headline", "to": "style_pass", "kind": "always", "label": "polish", "when": "Always after the editor ships."},
    {"from": "style_pass", "to": "final_rewrite", "kind": "always", "label": "cleanup", "when": "Always after the finishing style pass."},
    {"from": "final_rewrite", "to": "grounding_recheck", "kind": "always", "label": "verify sources", "when": "Always. The finished draft is checked against uploads."},
    {"from": "grounding_recheck", "to": "human_gate", "kind": "exit", "label": "grounded", "when": "If the draft still matches the sources, or drift retries are exhausted."},
    {"from": "grounding_recheck", "to": "final_rewrite", "kind": "loop", "label": "still drifting", "when": "If grounding finds drift and it has retried fewer than twice."},
    {"from": "human_gate", "to": "export", "kind": "exit", "label": "approved", "when": "If you approve the article."},
    {"from": "human_gate", "to": "rewrite", "kind": "hitl", "label": "changes requested", "when": "If you send the draft back with notes. Those notes become a critical finding."},
]

_ITER_RE = re.compile(r"Iteration (\d+): (\d+) open")
_REVIEWER_RE = re.compile(r"(\d+) finding")


def word_count(markdown: str) -> int:
    return len(re.findall(r"\b\w+\b", markdown or ""))


def excerpt(markdown: str, limit: int = 420) -> str:
    text = re.sub(r"^#+\s+", "", markdown or "", flags=re.M)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"[*`>_]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _as_finding(item: Any) -> Finding | None:
    if isinstance(item, Finding):
        return item
    if isinstance(item, dict):
        try:
            return Finding.model_validate(item)
        except Exception:
            return None
    return None


def _finding_counts(findings: list[Any]) -> tuple[dict[str, int], dict[str, int], list[Finding]]:
    parsed: list[Finding] = []
    by_reviewer: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in findings:
        finding = _as_finding(item)
        if finding is None:
            continue
        parsed.append(finding)
        role = finding.reviewer.value if hasattr(finding.reviewer, "value") else str(finding.reviewer)
        sev = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        by_reviewer[role] = by_reviewer.get(role, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return by_reviewer, by_severity, parsed


def make_snapshot(
    *,
    iteration: int,
    phase: str,
    markdown: str,
    findings: list[Any] | None = None,
    summary: str = "",
) -> IterationSnapshot:
    by_reviewer, by_severity, parsed = _finding_counts(findings or [])
    md = markdown or ""
    return IterationSnapshot(
        iteration=iteration,
        phase=phase,
        summary=summary or f"{phase} at iteration {iteration}",
        markdown=md,
        excerpt=excerpt(md),
        word_count=word_count(md),
        char_count=len(md),
        open_findings_count=len(parsed),
        findings=parsed,
        findings_by_reviewer=by_reviewer,
        findings_by_severity=by_severity,
    )


def events_from_logs(logs: list[Any]) -> list[NodeEvent]:
    events: list[NodeEvent] = []
    for item in logs or []:
        if isinstance(item, LogEntry):
            events.append(
                NodeEvent(
                    node=item.node,
                    message=item.message,
                    iteration=item.iteration or 0,
                    timestamp=item.timestamp or utc_now_iso(),
                    level=item.level.value if hasattr(item.level, "value") else str(item.level),
                )
            )
        elif isinstance(item, dict):
            events.append(
                NodeEvent(
                    node=str(item.get("node") or "unknown"),
                    message=str(item.get("message") or ""),
                    iteration=int(item.get("iteration") or 0),
                    timestamp=str(item.get("timestamp") or utc_now_iso()),
                    level=str(item.get("level") or "info"),
                )
            )
    return events


def node_visits(events: list[NodeEvent]) -> dict[str, int]:
    """Count executions, not log lines. One visit per node per review iteration."""
    seen: dict[str, set[int]] = {}
    for event in events:
        seen.setdefault(event.node, set()).add(int(event.iteration or 0))
    return {node: len(iterations) for node, iterations in seen.items()}


def history_from_logs(logs: list[Any], markdown: str = "") -> list[IterationSnapshot]:
    """Rebuild a findings series when older runs did not store snapshots."""
    snapshots: list[IterationSnapshot] = []
    by_iter: dict[int, IterationSnapshot] = {}
    reviewer_bucket: dict[int, dict[str, int]] = {}
    current_iter = 0
    for event in events_from_logs(logs):
        match = _ITER_RE.search(event.message)
        if event.node.startswith("reviewer_"):
            found = _REVIEWER_RE.search(event.message)
            if found:
                role = event.node.replace("reviewer_", "")
                bucket = reviewer_bucket.setdefault(current_iter, {})
                bucket[role] = bucket.get(role, 0) + int(found.group(1))
        if match:
            current_iter = int(match.group(1))
            count = int(match.group(2))
            by_iter[current_iter] = IterationSnapshot(
                iteration=current_iter,
                phase="review",
                summary=f"{count} open findings after review",
                markdown=markdown if current_iter == max(by_iter.keys(), default=current_iter) else "",
                excerpt=excerpt(markdown) if current_iter == max([current_iter, *by_iter.keys()]) else "",
                word_count=word_count(markdown) if not by_iter else 0,
                char_count=len(markdown) if not by_iter else 0,
                open_findings_count=count,
                findings_by_reviewer=reviewer_bucket.get(current_iter, {}),
                timestamp=event.timestamp,
            )
        elif event.node == "draft" and "Draft generated" in event.message:
            by_iter.setdefault(
                0,
                IterationSnapshot(
                    iteration=0,
                    phase="draft",
                    summary=event.message,
                    timestamp=event.timestamp,
                ),
            )
        elif event.node == "rewrite" and "complete" in event.message:
            by_iter.setdefault(
                event.iteration or current_iter,
                IterationSnapshot(
                    iteration=event.iteration or current_iter,
                    phase="rewrite",
                    summary=event.message,
                    timestamp=event.timestamp,
                ),
            )
    last = max(by_iter.keys(), default=None)
    if last is not None and markdown:
        by_iter[last].markdown = markdown
        by_iter[last].excerpt = excerpt(markdown)
        by_iter[last].word_count = word_count(markdown)
        by_iter[last].char_count = len(markdown)
    snapshots = [by_iter[key] for key in sorted(by_iter)]
    return snapshots


def findings_series(history: list[IterationSnapshot]) -> list[dict[str, Any]]:
    series: list[dict[str, Any]] = []
    for item in history:
        if item.phase not in ("review", "cap"):
            continue
        series.append(
            {
                "iteration": item.iteration,
                "phase": item.phase,
                "open": item.open_findings_count,
                "critical": item.findings_by_severity.get("critical", 0),
                "major": item.findings_by_severity.get("major", 0),
                "minor": item.findings_by_severity.get("minor", 0),
                "word_count": item.word_count,
            }
        )
    return series


def title_from_state(state: dict[str, Any]) -> str:
    plan = state.get("plan")
    if plan is not None:
        title = getattr(plan, "title", None) or (plan.get("title") if isinstance(plan, dict) else "")
        if title:
            return str(title)
    md = state.get("final_markdown") or state.get("draft_markdown") or ""
    match = re.search(r"^#\s+(.+)$", md, re.M)
    return match.group(1).strip() if match else ""


def build_run_trace(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    logs = state.get("logs") or []
    markdown = state.get("final_markdown") or state.get("draft_markdown") or ""
    stored = state.get("iteration_history") or []
    history: list[IterationSnapshot] = []
    for item in stored:
        if isinstance(item, IterationSnapshot):
            history.append(item)
        elif isinstance(item, dict):
            try:
                history.append(IterationSnapshot.model_validate(item))
            except Exception:
                continue
    # Older runs (and any run whose snapshots were dropped by a merge) keep only the
    # terminal snapshot. Rebuild the per-iteration series from the logs in that case.
    if not any(item.phase in ("review", "cap") for item in history):
        rebuilt = history_from_logs(logs, markdown)
        if rebuilt:
            tail = [item for item in history if item.phase not in ("review", "cap")]
            history = rebuilt + tail
    events = events_from_logs(logs)
    stored_events = state.get("node_events") or []
    if stored_events and not events:
        events = [
            ev if isinstance(ev, NodeEvent) else NodeEvent.model_validate(ev)
            for ev in stored_events
        ]
    open_findings = [_as_finding(f) for f in state.get("open_findings") or []]
    accepted = [_as_finding(f) for f in state.get("accepted_findings") or []]
    resolved = [_as_finding(f) for f in state.get("resolved_findings") or []]
    open_findings = [f for f in open_findings if f is not None]
    accepted = [f for f in accepted if f is not None]
    resolved = [f for f in resolved if f is not None]
    if not accepted and (state.get("cap_hit_with_open_findings") or state.get("stalled")):
        accepted = open_findings
    visits = node_visits(events)
    # Prefer the node that is running now. Last log is the last *finished*
    # node, which is why the UI used to sit on Draft during image_gen.
    current = str(state.get("current_node") or "").strip()
    last_finished = events[-1].node if events else ""
    last_node = current or last_finished
    return {
        "title": title_from_state(state),
        "max_iterations": settings.max_review_iterations,
        "last_node": last_node,
        "node_visits": visits,
        "node_events": events,
        "iterations": history,
        "findings_series": findings_series(history),
        "open_findings": open_findings,
        "accepted_findings": accepted,
        "resolved_findings": resolved,
        "editor_score": state.get("editor_score") or 0,
        "editor_notes": state.get("editor_notes") or "",
        "graph": {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES, "phases": GRAPH_PHASES},
    }
