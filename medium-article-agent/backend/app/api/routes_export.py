"""Export API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes_pipeline import _run_states
from app.graph.state import ExportArtifacts
from app.schemas.api_models import ExportResponse

router = APIRouter()


@router.get("/{run_id}", response_model=ExportResponse)
async def get_export(run_id: str):
    state = _run_states.get(run_id, {})
    export = state.get("export")
    if not export:
        raise HTTPException(404, "Export not ready")
    if isinstance(export, ExportArtifacts):
        return ExportResponse(run_id=run_id, export=export)
    return ExportResponse(run_id=run_id, export=ExportArtifacts(**export))


@router.get("/{run_id}/clipboard")
async def get_clipboard(run_id: str):
    state = _run_states.get(run_id, {})
    export = state.get("export")
    if not export:
        raise HTTPException(404, "Export not ready")
    text = export.clipboard_text if isinstance(export, ExportArtifacts) else export.get("clipboard_text", "")
    return {"clipboard_text": text}
