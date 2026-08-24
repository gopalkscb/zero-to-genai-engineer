"""Deterministic Medium house-skill lint. No LLM. Stable finding IDs."""

from __future__ import annotations

from app.editorial.skills import lint_article
from app.graph.state import AgentState, Finding, LogEntry, LogLevel, ReviewerRole, Severity


def skills_lint_node(state: AgentState) -> dict:
    draft = state.get("draft_markdown") or state.get("final_markdown") or ""
    iteration = state.get("iteration", 0)
    previous = [
        item
        for item in state.get("open_findings", []) or []
        if getattr(item, "reviewer", None) == ReviewerRole.SKILLS and not getattr(item, "resolved", False)
    ]
    audit = lint_article(draft, skills_rules=state.get("skills_rules") or "", images=state.get("images") or [])

    findings: list[Finding] = []
    failed = [item for item in audit.checks if not item.passed]
    for item in failed:
        finding_id = f"skills-{item.check_id}"
        findings.append(
            Finding(
                finding_id=finding_id,
                reviewer=ReviewerRole.SKILLS,
                severity=Severity(item.severity if item.severity in ("critical", "major", "minor") else "minor"),
                problem=item.problem or item.label,
                suggested_fix=item.suggested_fix or item.label,
                resolved=False,
                review_iteration=iteration,
            )
        )

    # Mark previously open skills findings resolved when the check now passes.
    passed_ids = {f"skills-{item.check_id}" for item in audit.checks if item.passed}
    for item in previous:
        if item.finding_id in passed_ids:
            findings.append(
                Finding(
                    finding_id=item.finding_id,
                    reviewer=ReviewerRole.SKILLS,
                    severity=item.severity,
                    problem=item.problem,
                    suggested_fix=item.suggested_fix,
                    resolved=True,
                    review_iteration=iteration,
                )
            )

    open_now = [item for item in findings if not item.resolved]
    return {
        "new_findings": findings,
        "skills_audit": audit.as_dict(),
        "logs": [
            LogEntry(
                node="reviewer_skills",
                level=LogLevel.INFO if not open_now else LogLevel.WARNING,
                message=(
                    f"House skill lint: {audit.as_dict()['passed']} passed, "
                    f"{len(failed)} open ({', '.join(item.check_id for item in failed[:6]) or 'clean'})"
                ),
                iteration=iteration,
            )
        ],
    }
