"""Pipeline API routes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.events.event_bus import event_bus
from app.graph import runtime
from app.graph.build_graph import build_graph
from app.graph.checkpointer import async_checkpointer
from app.graph.images import inject_images
from app.graph.nodes.supervisor import blocking_findings
from app.graph.state import (
    HumanFeedback,
    ImageAsset,
    ImageStatus,
    IterationSnapshot,
    LogEntry,
    LogLevel,
    PipelineStatus,
)
from app.graph.trace import build_run_trace
from app.persistence.repository import RunRepository
from app.persistence.snapshot import snapshot_for_db
from app.schemas.api_models import (
    ApproveRequest,
    ApproveResponse,
    ConfigStatusResponse,
    PipelineStartResponse,
    ResumeResponse,
    RunStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()
_repo = RunRepository()
_run_states: dict[str, dict[str, Any]] = {}

# After a node returns, stream_mode="updates" is silent until the next node
# returns. These hints jump the UI cursor to the next linear step immediately.
_NEXT_HINT = {
    "ingest": "plan",
    "plan": "web_research",
    "web_research": "draft",
    "draft": "image_gen",
    "image_gen": "image_review",
    "image_redraw": "image_review",
    "rewrite": "rewrite_voice",
    "headline": "style_pass",
    "style_pass": "final_rewrite",
    "final_rewrite": "grounding_recheck",
}


def _status_value(raw: Any) -> PipelineStatus:
    if isinstance(raw, PipelineStatus):
        return raw
    try:
        return PipelineStatus(str(raw))
    except ValueError:
        return PipelineStatus.PENDING


def _coerce_images(raw: Any) -> list[ImageAsset]:
    images: list[ImageAsset] = []
    for img in raw or []:
        if isinstance(img, ImageAsset):
            images.append(img)
        elif isinstance(img, dict):
            try:
                images.append(ImageAsset.model_validate(img))
            except Exception:
                continue
    return images


def _log_identity(item: Any) -> tuple[Any, Any, Any]:
    if hasattr(item, "timestamp"):
        return (item.timestamp, item.node, item.message)
    if isinstance(item, dict):
        return (item.get("timestamp"), item.get("node"), item.get("message"))
    return (id(item), None, str(item))


def _extend_unique(prev: list, incoming: list) -> list:
    merged = list(prev or [])
    seen = {_log_identity(item) for item in merged}
    for item in incoming or []:
        key = _log_identity(item)
        if key in seen:
            continue
        merged.append(item)
        seen.add(key)
    return merged


async def _load_graph_state(run_id: str) -> dict[str, Any]:
    config = {"configurable": {"thread_id": run_id}}
    try:
        async with async_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            snap = await graph.aget_state(config)
            values = getattr(snap, "values", None) or {}
            payload = dict(values) if values else {}
            nxt = list(getattr(snap, "next", None) or [])
            if nxt and not payload.get("current_node"):
                payload["current_node"] = nxt[0]
                payload["progress_hint"] = runtime.hint_for(nxt[0])
            payload["_checkpoint_next"] = nxt
            return payload
    except Exception:
        logger.exception("Failed to load checkpoint for %s", run_id)
        return {}


async def _checkpoint_next(run_id: str) -> list[str]:
    state = await _load_graph_state(run_id)
    return list(state.get("_checkpoint_next") or [])


async def _resolve_state(run_id: str) -> dict[str, Any]:
    memory = dict(_run_states.get(run_id) or {})
    record = _repo.get_run(run_id)
    snap = dict(record.state_snapshot) if record is not None and record.state_snapshot else {}
    state = {**snap, **memory}
    if memory.get("logs"):
        state["logs"] = memory["logs"]
    if memory.get("final_markdown"):
        state["final_markdown"] = memory["final_markdown"]
    if memory.get("images"):
        state["images"] = memory["images"]
    if memory.get("current_node"):
        state["current_node"] = memory["current_node"]

    has_article = bool(state.get("final_markdown") or state.get("draft_markdown"))
    if not has_article:
        graph_state = await _load_graph_state(run_id)
        if graph_state:
            merged = {**graph_state, **state}
            if not (merged.get("final_markdown") or merged.get("draft_markdown")):
                merged["final_markdown"] = (
                    graph_state.get("final_markdown") or graph_state.get("draft_markdown") or ""
                )
            graph_images = _coerce_images(graph_state.get("images"))
            if graph_images:
                merged["images"] = graph_state["images"]
            state = merged

    if record is not None and not state.get("status"):
        state["status"] = record.status
    if (
        record is not None
        and (state.get("final_markdown") or state.get("draft_markdown"))
        and not (record.state_snapshot or {}).get("final_markdown")
        and not (record.state_snapshot or {}).get("draft_markdown")
    ):
        _repo.update_run(
            run_id,
            _status_value(state.get("status")).value,
            state_snapshot=snapshot_for_db(state),
        )
    return state


async def _emit_logs(run_id: str, logs: list):
    for log in logs:
        payload = log.model_dump() if hasattr(log, "model_dump") else log
        await event_bus.publish(run_id, {"type": "log", "data": payload})


def _persist_progress(run_id: str, snapshot: dict[str, Any]) -> None:
    _repo.update_run(run_id, "running", state_snapshot=snapshot_for_db(snapshot))


# Fields declared with operator.add in AgentState. A stream_mode="updates" event
# carries only the delta for these, so a plain dict merge would drop the history.
_APPEND_ONLY_KEYS = ("logs", "iteration_history", "node_events", "new_findings")


def _merge_update(prev: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = {**prev, **update}
    for key in _APPEND_ONLY_KEYS:
        if key in update:
            if key == "logs":
                merged[key] = _extend_unique(prev.get(key) or [], update.get(key) or [])
            else:
                merged[key] = list(prev.get(key) or []) + list(update.get(key) or [])
    return merged


def _seed_runtime(run_id: str, seed: dict[str, Any]) -> None:
    _run_states[run_id] = seed
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    runtime.bind(loop=loop, states=_run_states, emit=_emit_logs, persist=_persist_progress)


async def _run_pipeline(
    run_id: str,
    uploaded_files: list[dict],
    topic_hint: str,
    enable_web_research: bool = False,
    resume: bool = False,
):
    if not runtime.mark_active(run_id):
        logger.info("Run %s is already active in this process", run_id)
        return
    config = {"configurable": {"thread_id": run_id}}
    record = _repo.get_run(run_id)
    seed = dict(record.state_snapshot) if resume and record is not None and record.state_snapshot else {}
    seed["status"] = PipelineStatus.RUNNING
    seed["error"] = ""
    if not resume:
        seed["logs"] = list(seed.get("logs") or [])
    _seed_runtime(run_id, seed)
    _repo.update_run(run_id, "running", state_snapshot=snapshot_for_db(seed))
    try:
        async with async_checkpointer() as checkpointer:
            graph = build_graph(checkpointer=checkpointer)
            input_state: dict[str, Any] | None
            if resume:
                snap = await graph.aget_state(config)
                nxt = list(getattr(snap, "next", None) or [])
                values = dict(getattr(snap, "values", None) or {})
                if values:
                    merged = _merge_update(seed, values)
                    merged["status"] = PipelineStatus.RUNNING
                    _run_states[run_id] = merged
                if not nxt:
                    if values.get("export") or _status_value(values.get("status")) == PipelineStatus.COMPLETED:
                        current = {**(_run_states.get(run_id) or {}), "status": PipelineStatus.COMPLETED}
                        _run_states[run_id] = current
                        _repo.update_run(run_id, "completed", state_snapshot=snapshot_for_db(current))
                        return
                    raise RuntimeError(
                        "This job has no LangGraph checkpoint to resume. "
                        "The worker died before the first node finished. Start a new run."
                    )
                if "human_gate" in nxt:
                    current = {
                        **(_run_states.get(run_id) or values),
                        "status": PipelineStatus.PAUSED_HITL,
                        "current_node": "human_gate",
                    }
                    _run_states[run_id] = current
                    _repo.update_run(run_id, "paused_hitl", state_snapshot=snapshot_for_db(current))
                    return
                runtime.report(
                    run_id,
                    nxt[0],
                    f"Resuming LangGraph at {nxt[0]}. Checkpoint was waiting here after the last restart.",
                )
                input_state = None
            else:
                input_state = {
                    "run_id": run_id,
                    "uploaded_files": uploaded_files,
                    "topic_hint": topic_hint,
                    "enable_web_research": enable_web_research,
                    "status": PipelineStatus.RUNNING,
                    "current_node": "ingest",
                }
                runtime.set_current_node(run_id, "ingest")
            try:
                async for chunk in graph.astream(
                    input_state,
                    config=config,
                    stream_mode=["updates", "tasks"],
                ):
                    mode, data = chunk if isinstance(chunk, tuple) else ("updates", chunk)
                    if mode == "tasks":
                        payload = data if isinstance(data, dict) else {}
                        name = str(payload.get("name") or "")
                        # TaskPayload has triggers; TaskResultPayload has result.
                        if name and "triggers" in payload:
                            runtime.set_current_node(run_id, name)
                        continue
                    if mode != "updates" or not isinstance(data, dict):
                        continue
                    for node_name, update in data.items():
                        if not update or str(node_name).startswith("__"):
                            continue
                        if not isinstance(update, dict):
                            continue
                        new_logs = update.get("logs") or []
                        if new_logs:
                            await _emit_logs(run_id, new_logs)
                        prev = _run_states.get(run_id, {})
                        merged = _merge_update(prev, update)
                        nxt_hint = _NEXT_HINT.get(str(node_name))
                        merged["current_node"] = update.get("current_node") or nxt_hint or node_name
                        if nxt_hint:
                            merged["progress_hint"] = runtime.hint_for(nxt_hint)
                        _run_states[run_id] = merged
                        for snap in update.get("iteration_history") or []:
                            md = snap.markdown if hasattr(snap, "markdown") else (snap or {}).get("markdown", "")
                            it = snap.iteration if hasattr(snap, "iteration") else (snap or {}).get("iteration", 0)
                            if md:
                                _repo.save_draft_snapshot(run_id, int(it), md)
                        _repo.update_run(run_id, "running", state_snapshot=snapshot_for_db(merged))
            except Exception as exc:
                # interrupt_before / GraphInterrupt is a pause, not a crash
                name = type(exc).__name__
                if "Interrupt" not in name and "interrupt" not in str(exc).lower():
                    raise
        current = _run_states.get(run_id, {})
        if current.get("status") not in (PipelineStatus.COMPLETED, PipelineStatus.FAILED):
            current["status"] = PipelineStatus.PAUSED_HITL
            current["current_node"] = "human_gate"
            _run_states[run_id] = current
        _repo.update_run(run_id, "paused_hitl", state_snapshot=snapshot_for_db(current))
    except Exception as exc:
        logger.exception("Pipeline failed for run %s", run_id)
        fail_log = LogEntry(
            node="pipeline",
            level=LogLevel.ERROR,
            message=f"Pipeline failed: {exc}",
        )
        prev = _run_states.get(run_id, {})
        prev_logs = list(prev.get("logs", []))
        prev_logs.append(fail_log)
        failed_state = {
            **prev,
            "status": PipelineStatus.FAILED,
            "error": str(exc),
            "logs": prev_logs,
        }
        _run_states[run_id] = failed_state
        _repo.update_run(run_id, "failed", state_snapshot=snapshot_for_db(failed_state))
        await event_bus.publish(run_id, {"type": "error", "data": {"message": str(exc)}})
        await _emit_logs(run_id, [fail_log])
    finally:
        runtime.mark_done(run_id)


def _kickoff(
    background_tasks: BackgroundTasks,
    run_id: str,
    uploaded_files: list[dict],
    topic_hint: str,
    enable_web_research: bool,
    resume: bool = False,
) -> None:
    background_tasks.add_task(
        _run_pipeline, run_id, uploaded_files, topic_hint, enable_web_research, resume
    )


async def maybe_resume_orphan(run_id: str, background_tasks: BackgroundTasks) -> list[str]:
    """If the worker died, continue from the LangGraph checkpoint.

    GET /status polls this. Opening the stuck Draft URL is enough to unstick it.
    """
    if runtime.in_pytest() or runtime.is_active(run_id):
        return []
    record = _repo.get_run(run_id)
    if record is None or record.status != "running":
        return []
    nxt = await _checkpoint_next(run_id)
    if not nxt or "human_gate" in nxt:
        return nxt
    logger.warning("Orphaned run %s is still marked running; resuming at %s", run_id, nxt)
    _kickoff(background_tasks, run_id, [], record.topic_hint or "", False, True)
    return nxt


@router.get("/config", response_model=ConfigStatusResponse)
async def get_config_status():
    settings = get_settings()
    return ConfigStatusResponse(
        style_guide=settings.style_guide_status(),
        llm_provider=settings.llm_provider,
        image_count=settings.image_count,
        max_review_iterations=settings.max_review_iterations,
    )


@router.get("/recent")
async def recent_runs():
    return {"runs": _repo.list_recent(20)}


@router.post("/start", response_model=PipelineStartResponse)
async def start_pipeline(
    background_tasks: BackgroundTasks,
    topic_hint: str = Form(""),
    enable_web_research: bool = Form(False),
    files: list[UploadFile] = File(...),
):
    run_id = _repo.create_run(topic_hint)
    uploaded = []
    for idx, f in enumerate(files):
        content = await f.read()
        uploaded.append(
            {
                "content": content,
                "filename": f.filename or f"file_{idx}",
                "source_id": f"src{idx + 1}",
            }
        )
    _kickoff(background_tasks, run_id, uploaded, topic_hint, enable_web_research, False)
    return PipelineStartResponse(run_id=run_id, status=PipelineStatus.RUNNING)


@router.post("/{run_id}/resume", response_model=ResumeResponse)
async def resume_run(run_id: str, background_tasks: BackgroundTasks):
    record = _repo.get_run(run_id)
    if record is None:
        raise HTTPException(404, "Run not found")
    if runtime.is_active(run_id):
        return ResumeResponse(
            run_id=run_id,
            status=PipelineStatus.RUNNING,
            resumed=False,
            detail="Already running in this process",
        )
    status = record.status or ""
    if status in ("completed", "failed"):
        raise HTTPException(409, f"Run is {status} and cannot be resumed")
    if status == "paused_hitl":
        raise HTTPException(409, "Paused for human review — use approve, not resume")
    nxt = await _checkpoint_next(run_id)
    if "human_gate" in nxt:
        raise HTTPException(409, "Paused for human review — use approve, not resume")
    if not nxt:
        raise HTTPException(
            409,
            "No LangGraph checkpoint to resume. The worker died before the first node finished.",
        )
    _kickoff(background_tasks, run_id, [], record.topic_hint or "", False, True)
    return ResumeResponse(
        run_id=run_id,
        status=PipelineStatus.RUNNING,
        resumed=True,
        next_nodes=nxt,
        detail=f"Resuming at {nxt[0]}",
    )


@router.get("/{run_id}/status", response_model=RunStatusResponse)
async def get_status(run_id: str, background_tasks: BackgroundTasks):
    nxt = await maybe_resume_orphan(run_id, background_tasks)
    state = await _resolve_state(run_id)
    if nxt and not state.get("current_node"):
        state["current_node"] = nxt[0]
        state["progress_hint"] = runtime.hint_for(nxt[0])
    record = _repo.get_run(run_id)
    status = state.get("status")
    if status is None and record is not None:
        status = record.status
    images = _coerce_images(state.get("images"))
    markdown = state.get("final_markdown") or state.get("draft_markdown") or ""
    markdown = inject_images(markdown, images)
    trace = build_run_trace({**state, "final_markdown": markdown})
    plan = state.get("plan")
    subtitle = ""
    tags: list[str] = []
    if plan is not None:
        subtitle = getattr(plan, "subtitle", None) or (plan.get("subtitle") if isinstance(plan, dict) else "") or ""
        tags = getattr(plan, "tags", None) or (plan.get("tags") if isinstance(plan, dict) else []) or []
    slim_iters: list[IterationSnapshot] = []
    for item in trace["iterations"]:
        dumped = item.model_dump()
        dumped["markdown"] = ""
        slim_iters.append(IterationSnapshot.model_validate(dumped))
    current = str(state.get("current_node") or trace["last_node"] or "")
    hint = str(state.get("progress_hint") or runtime.hint_for(current) if current else "")
    return RunStatusResponse(
        run_id=run_id,
        status=_status_value(status),
        iteration=state.get("iteration", 0),
        open_findings_count=len(state.get("open_findings", [])),
        blocking_findings_count=len(blocking_findings(trace["open_findings"])),
        resolved_findings_count=len(trace["resolved_findings"]),
        converged=state.get("converged", False),
        cap_hit_with_open_findings=state.get("cap_hit_with_open_findings", False),
        stalled=state.get("stalled", False),
        logs=state.get("logs", []),
        error=state.get("error", ""),
        final_markdown=markdown,
        images=images,
        title=trace["title"],
        max_iterations=trace["max_iterations"],
        last_node=current,
        progress_hint=hint,
        preview_url=f"/?run={run_id}",
        pipeline_url=f"/?run={run_id}&view=pipeline",
        node_visits=trace["node_visits"],
        findings_series=trace["findings_series"],
        iterations=slim_iters,
        open_findings=trace["open_findings"],
        accepted_findings=trace["accepted_findings"],
        resolved_findings=trace["resolved_findings"],
        graph=trace["graph"],
        node_events=trace["node_events"],
        editor_score=float(trace.get("editor_score") or 0),
        editor_notes=str(trace.get("editor_notes") or ""),
        parse_report=state.get("parse_report") or {},
        skills_audit=state.get("skills_audit") or {},
        subtitle=str(subtitle or ""),
        tags=[str(tag) for tag in tags],
    )


@router.get("/{run_id}/iterations/{iteration}")
async def get_iteration(run_id: str, iteration: int, phase: str | None = None):
    state = await _resolve_state(run_id)
    markdown = state.get("final_markdown") or state.get("draft_markdown") or ""
    trace = build_run_trace({**state, "final_markdown": markdown})
    matches = [item for item in trace["iterations"] if item.iteration == iteration]
    if phase:
        matches = [item for item in matches if item.phase == phase] or matches
    if not matches:
        raise HTTPException(404, "Iteration not found")
    pick = next((item for item in reversed(matches) if item.markdown), matches[-1])
    if not pick.markdown:
        drafts = _repo.list_drafts(run_id)
        for draft in reversed(drafts):
            if str(draft.get("iteration")) == str(iteration) and draft.get("markdown"):
                pick.markdown = draft["markdown"]
                break
    if not pick.markdown and iteration == int(state.get("iteration") or 0):
        pick.markdown = markdown
    return pick


@router.get("/{run_id}/images/{image_id}.png")
async def serve_image(run_id: str, image_id: str):
    if any(part in image_id for part in ("/", "\\", "..")):
        raise HTTPException(400, "Invalid image id")
    settings = get_settings()
    path = settings.data_dir / "runs" / run_id / "images" / f"{image_id}.png"
    if not path.exists():
        raise HTTPException(404, "Image not found")
    return FileResponse(path, media_type="image/png")


@router.post("/{run_id}/approve", response_model=ApproveResponse)
async def approve_run(run_id: str, body: ApproveRequest):
    config = {"configurable": {"thread_id": run_id}}
    feedback = HumanFeedback(approved=body.approved, change_notes=body.change_notes)
    async with async_checkpointer() as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        await graph.aupdate_state(config, {"human_feedback": feedback})
        result = await graph.ainvoke(None, config=config)
    _run_states[run_id] = result
    status = result.get("status", PipelineStatus.COMPLETED)
    _repo.update_run(
        run_id,
        status.value if hasattr(status, "value") else str(status),
        state_snapshot=snapshot_for_db(result),
    )
    return ApproveResponse(run_id=run_id, status=_status_value(status))
