"""Live pipeline progress that does not wait for a LangGraph node to return.

LangGraph `stream_mode="updates"` only emits after a node function returns.
`image_gen` can spend minutes inside OpenAI before that happens, so the UI
looks frozen on whatever node last finished (usually Draft). This module
lets nodes publish `current_node` + logs immediately, including from worker
threads, and guards against double-running the same job after a reload.
"""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.graph.state import LogEntry, LogLevel, PipelineStatus

EmitFn = Callable[[str, list[LogEntry]], Awaitable[None]]
PersistFn = Callable[[str, dict[str, Any]], None]

_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None
_states: dict[str, dict[str, Any]] | None = None
_emit: EmitFn | None = None
_persist: PersistFn | None = None
_active: set[str] = set()

PROGRESS_HINTS = {
    "ingest": "Reading sources and the house style guide.",
    "plan": "Planning the article. This LLM call can take a minute.",
    "web_research": "Gathering optional web snippets.",
    "draft": "Writing the first draft. This LLM call can take a minute.",
    "image_gen": "Generating HD figures. Each image can take 1–2 minutes — the graph is working, not stuck.",
    "image_review": "Vision-checking figures.",
    "image_redraw": "Redrawing rejected figures. Each redraw can take a minute.",
    "reviewer_technical": "Technical review in progress.",
    "reviewer_style": "Style review in progress.",
    "reviewer_structure": "Structure review in progress.",
    "reviewer_grounding": "Grounding review in progress.",
    "reviewer_reader": "Reader review in progress.",
    "reviewer_skills": "House-skill lint in progress.",
    "supervisor": "Supervisor is deciding the next loop.",
    "rewrite": "Rewriting from open findings. This LLM call can take a minute.",
    "rewrite_voice": "Voice pass on the rewrite.",
    "editor_score": "Editor is scoring the draft.",
    "headline": "Rewriting the headline.",
    "style_pass": "Style polish pass.",
    "final_rewrite": "Final rewrite before grounding recheck.",
    "grounding_recheck": "Rechecking claims against the sources.",
    "human_gate": "Waiting for your approval.",
    "export": "Exporting the article.",
}


def in_pytest() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def bind(
    *,
    loop: asyncio.AbstractEventLoop | None = None,
    states: dict[str, dict[str, Any]] | None = None,
    emit: EmitFn | None = None,
    persist: PersistFn | None = None,
) -> None:
    global _loop, _states, _emit, _persist
    if loop is not None:
        _loop = loop
    if states is not None:
        _states = states
    if emit is not None:
        _emit = emit
    if persist is not None:
        _persist = persist


def reset() -> None:
    """Tests only — drop process-local runtime bindings."""
    global _loop, _states, _emit, _persist
    with _lock:
        _active.clear()
        _loop = None
        _states = None
        _emit = None
        _persist = None


def mark_active(run_id: str) -> bool:
    """Return False if this process is already executing the run."""
    with _lock:
        if run_id in _active:
            return False
        _active.add(run_id)
        return True


def mark_done(run_id: str) -> None:
    with _lock:
        _active.discard(run_id)


def is_active(run_id: str) -> bool:
    with _lock:
        return run_id in _active


def hint_for(node: str) -> str:
    return PROGRESS_HINTS.get(node, f"Running {node.replace('_', ' ')}.")


def report(
    run_id: str,
    node: str,
    message: str,
    *,
    level: LogLevel = LogLevel.INFO,
    extra: dict[str, Any] | None = None,
    log: bool = True,
) -> LogEntry:
    """Publish live progress. Safe to call from a graph node or a worker thread."""
    entry = LogEntry(node=node, level=level, message=message)
    if _states is None:
        return entry
    with _lock:
        prev = dict(_states.get(run_id) or {})
        if log:
            logs = list(prev.get("logs") or [])
            logs.append(entry)
            prev["logs"] = logs
        prev["current_node"] = node
        prev["progress_hint"] = hint_for(node)
        prev["progress_at"] = datetime.now(timezone.utc).isoformat()
        prev["status"] = prev.get("status") or PipelineStatus.RUNNING
        if extra:
            prev.update(extra)
        _states[run_id] = prev
        snapshot = dict(prev)
    _schedule_emit(run_id, [entry] if log else [])
    _persist_snapshot(run_id, snapshot)
    return entry


def set_current_node(run_id: str, node: str) -> None:
    """Move the UI to `node` without adding a log line."""
    report(run_id, node, hint_for(node), log=False)


def _schedule_emit(run_id: str, logs: list[LogEntry]) -> None:
    if not logs or _emit is None or _loop is None:
        return
    try:
        asyncio.run_coroutine_threadsafe(_emit(run_id, logs), _loop)
    except RuntimeError:
        pass


def _persist_snapshot(run_id: str, snapshot: dict[str, Any]) -> None:
    if _persist is None:
        return
    try:
        _persist(run_id, snapshot)
    except Exception:
        pass
