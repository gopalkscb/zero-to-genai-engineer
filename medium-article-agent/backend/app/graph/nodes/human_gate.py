"""Human-in-the-loop gate.

Pause is done with interrupt_before=['human_gate'] in build_graph.
This node only runs after the API writes HumanFeedback and resumes.
"""

from __future__ import annotations

import uuid

from app.graph.state import (
    AgentState,
    Finding,
    HumanFeedback,
    LogEntry,
    LogLevel,
    PipelineStatus,
    ReviewerRole,
    Severity,
)


def human_gate_node(state: AgentState) -> dict:
    raw = state.get("human_feedback")
    if isinstance(raw, HumanFeedback):
        feedback = raw
    elif isinstance(raw, dict):
        feedback = HumanFeedback(
            approved=raw.get("approved", False),
            change_notes=raw.get("change_notes", ""),
        )
    else:
        feedback = HumanFeedback(approved=False)

    logs = [
        LogEntry(
            node="human_gate",
            level=LogLevel.INFO,
            message=f"Human feedback: approved={feedback.approved}",
        )
    ]

    result: dict = {
        "human_feedback": feedback,
        "status": PipelineStatus.RUNNING if feedback.approved else PipelineStatus.PAUSED_HITL,
        "logs": logs,
    }

    if not feedback.approved and feedback.change_notes:
        iteration = state.get("iteration", 0)
        synthetic = Finding(
            finding_id=str(uuid.uuid4())[:8],
            reviewer=ReviewerRole.STYLE,
            severity=Severity.CRITICAL,
            problem=feedback.change_notes,
            suggested_fix=feedback.change_notes,
            review_iteration=iteration,
        )
        prior = [
            item
            for item in (state.get("open_findings") or [])
            if not getattr(item, "resolved", False)
        ]
        result["open_findings"] = prior + [synthetic]
        result["new_findings"] = [synthetic]
        result["status"] = PipelineStatus.RUNNING
        result["editor_loop"] = False

    return result
