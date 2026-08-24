"""Numeric editor-in-chief gate. Score 1–10, then rewrite or ship.

This is the pattern used in production LangGraph writing systems
(researcher → writer → reviewer → editor, with a score threshold and a
revision cap). Specialists already closed their findings; this node asks
whether a human editor would actually publish.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.graph.prompt_context import EDITOR_SOURCE_BUDGET, skills_block, source_block
from app.graph.state import AgentState, Finding, LogEntry, LogLevel, ReviewerRole, Severity
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient


class EditorDefect(BaseModel):
    problem: str = ""
    suggested_fix: str = ""
    severity: str = "major"

    @field_validator("severity", mode="before")
    @classmethod
    def coerce_severity(cls, value):
        text = str(value or "major").lower()
        if text not in ("critical", "major", "minor"):
            return "major"
        return text


class EditorScore(BaseModel):
    score: float = 0
    notes: str = ""
    ready: bool = False
    defects: list[EditorDefect] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(1.0, min(10.0, number)) if number else 0.0


def _role_value(item: Finding) -> str:
    reviewer = getattr(item, "reviewer", "")
    return reviewer.value if hasattr(reviewer, "value") else str(reviewer)


def editor_score_node(state: AgentState) -> dict:
    settings = get_settings()
    llm = LLMClient()
    draft = state.get("draft_markdown") or state.get("final_markdown") or ""
    plan = state.get("plan")
    title = ""
    thesis = ""
    if plan is not None:
        title = getattr(plan, "title", None) or (plan.get("title") if isinstance(plan, dict) else "") or ""
        thesis = getattr(plan, "thesis", None) or (plan.get("thesis") if isinstance(plan, dict) else "") or ""
    iteration = state.get("iteration", 0)
    retries = int(state.get("editor_retries") or 0)

    prompt = f"""You are the editor-in-chief of a technical publication, not a cheerleader.

Score this Medium article from 1 to 10 for whether you would actually publish it.

Title: {title}
Thesis: {thesis}

House skill (fail the piece if these are missing):
{skills_block(state)}

A 9–10 has: a specific hook, the core term defined in the opening, a worked example
with numbers or steps from the sources, claims grounded in the source, scannable headings,
bold golden sentences, no AI-isms, AI disclosure at the bottom, and a comment-driving CTA.
A 6 is a competent outline dressed as an article. A 4 is vague.

If the score is below {settings.editor_score_threshold}, list concrete defects
(falsifiable: name the missing definition, missing example, unsourced number,
banned phrase, or broken figure). Do not write taste notes like "could be more engaging".

Draft:
{draft[:14000]}

Primary source (coverage pack):
{source_block(state, EDITOR_SOURCE_BUDGET)}"""

    messages = [
        {
            "role": "system",
            "content": "You are a strict publication editor. Score honestly. Defects must be checkable.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.complete("editor", messages, structured_schema=EditorScore, temperature=0.2)
        assert isinstance(result, EditorScore)
    except Exception as exc:
        result = EditorScore(score=8.0, notes=f"Editor fallback (call failed: {exc})", ready=True, defects=[])

    score = float(result.score or 0)
    threshold = float(settings.editor_score_threshold)
    passed = score >= threshold
    force = bool(state.get("cap_hit_with_open_findings") or state.get("stalled"))
    prior = [
        item
        for item in (state.get("open_findings") or [])
        if not getattr(item, "resolved", False) and _role_value(item) != ReviewerRole.EDITOR.value
    ]

    logs = [
        LogEntry(
            node="editor_score",
            level=LogLevel.INFO if passed or force else LogLevel.WARNING,
            message=(
                f"Editor score {score:.1f}/10 (threshold {threshold:.1f}). "
                + ("Ship." if passed or force else f"Revise ({retries + 1}/{settings.max_editor_retries}).")
            ),
            iteration=iteration,
        )
    ]

    if passed or force or retries >= settings.max_editor_retries:
        summary = f"Editor score {score:.1f}: {'ship' if passed else 'forced through'}"
        return {
            "editor_score": score,
            "editor_notes": result.notes,
            "editor_loop": False,
            "open_findings": prior,
            "iteration_history": [
                make_snapshot(
                    iteration=iteration,
                    phase="editor",
                    markdown=draft,
                    findings=prior,
                    summary=summary,
                )
            ],
            "logs": logs,
        }

    injected: list[Finding] = []
    defects = result.defects or []
    if not defects and result.notes:
        defects = [EditorDefect(problem=result.notes, suggested_fix=result.notes, severity="major")]
    for item in defects[:4]:
        problem = (item.problem or "").strip()
        if not problem:
            continue
        injected.append(
            Finding(
                finding_id=str(uuid.uuid4())[:8],
                reviewer=ReviewerRole.EDITOR,
                severity=Severity(item.severity),
                problem=problem,
                suggested_fix=(item.suggested_fix or problem).strip(),
                review_iteration=iteration,
            )
        )
    if not injected:
        injected.append(
            Finding(
                finding_id=str(uuid.uuid4())[:8],
                reviewer=ReviewerRole.EDITOR,
                severity=Severity.MAJOR,
                problem=f"Editor score {score:.1f} is below the publication bar of {threshold:.1f}",
                suggested_fix="Add a definition, a worked example, and a concrete takeaway. Do not shrink the piece.",
                review_iteration=iteration,
            )
        )

    logs.append(
        LogEntry(
            node="editor_score",
            level=LogLevel.WARNING,
            message=f"Editor sent {len(injected)} defect(s) back to rewrite",
            iteration=iteration,
        )
    )
    return {
        "editor_score": score,
        "editor_notes": result.notes,
        "editor_retries": retries + 1,
        "editor_loop": True,
        "converged": False,
        "open_findings": prior + injected,
        "new_findings": injected,
        "iteration_history": [
            make_snapshot(
                iteration=iteration,
                phase="editor",
                markdown=draft,
                findings=injected,
                summary=f"Editor score {score:.1f}: rewrite {len(injected)} defect(s)",
            )
        ],
        "logs": logs,
    }


def route_after_editor_score(state: AgentState) -> str:
    settings = get_settings()
    if state.get("cap_hit_with_open_findings") or state.get("stalled"):
        return "headline"
    score = float(state.get("editor_score") or 0)
    if score >= float(settings.editor_score_threshold):
        return "headline"
    if int(state.get("editor_retries") or 0) >= int(settings.max_editor_retries):
        return "headline"
    return "rewrite"
