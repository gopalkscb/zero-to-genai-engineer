"""API request/response models (Section 18)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.graph.state import (
    ExportArtifacts,
    Finding,
    ImageAsset,
    IterationSnapshot,
    LogEntry,
    NodeEvent,
    PipelineStatus,
    QuizItem,
)


class PipelineStartRequest(BaseModel):
    topic_hint: str = ""
    filenames: list[str] = Field(default_factory=list)


class PipelineStartResponse(BaseModel):
    run_id: str
    status: PipelineStatus


class RunStatusResponse(BaseModel):
    run_id: str
    status: PipelineStatus
    iteration: int = 0
    open_findings_count: int = 0
    blocking_findings_count: int = 0
    resolved_findings_count: int = 0
    converged: bool = False
    cap_hit_with_open_findings: bool = False
    stalled: bool = False
    logs: list[LogEntry] = Field(default_factory=list)
    error: str = ""
    final_markdown: str = ""
    images: list[ImageAsset] = Field(default_factory=list)
    title: str = ""
    max_iterations: int = 12
    last_node: str = ""
    progress_hint: str = ""
    preview_url: str = ""
    pipeline_url: str = ""
    node_visits: dict[str, int] = Field(default_factory=dict)
    findings_series: list[dict] = Field(default_factory=list)
    iterations: list[IterationSnapshot] = Field(default_factory=list)
    open_findings: list[Finding] = Field(default_factory=list)
    accepted_findings: list[Finding] = Field(default_factory=list)
    resolved_findings: list[Finding] = Field(default_factory=list)
    graph: dict = Field(default_factory=dict)
    node_events: list[NodeEvent] = Field(default_factory=list)
    editor_score: float = 0
    editor_notes: str = ""
    parse_report: dict = Field(default_factory=dict)
    skills_audit: dict = Field(default_factory=dict)
    subtitle: str = ""
    tags: list[str] = Field(default_factory=list)


class ApproveRequest(BaseModel):
    approved: bool = True
    change_notes: str = ""


class ApproveResponse(BaseModel):
    run_id: str
    status: PipelineStatus


class ResumeResponse(BaseModel):
    run_id: str
    status: PipelineStatus
    resumed: bool = True
    next_nodes: list[str] = Field(default_factory=list)
    detail: str = ""


class ExportResponse(BaseModel):
    run_id: str
    export: ExportArtifacts


class QuizSubmitRequest(BaseModel):
    answers: dict[str, int] = Field(default_factory=dict)


class QuizSubmitResponse(BaseModel):
    score: float
    total: int
    correct: int
    results: list[dict] = Field(default_factory=list)


class ConfigStatusResponse(BaseModel):
    style_guide: dict
    llm_provider: str
    image_count: int
    max_review_iterations: int = 12
