"""Section 5 hard contracts — shared between graph nodes and API."""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field, field_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Enums ---


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    IMAGE = "image"
    QUOTE = "quote"
    SLIDE = "slide"
    CELL = "cell"
    METADATA = "metadata"


class SourceFormat(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"
    HTML = "html"
    IPYNB = "ipynb"
    TRANSCRIPT = "transcript"
    TEXT = "text"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ReviewerRole(str, Enum):
    TECHNICAL = "technical"
    STYLE = "style"
    STRUCTURE = "structure"
    GROUNDING = "grounding"
    READER = "reader"
    SKILLS = "skills"
    EDITOR = "editor"


class ImageStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    SKIPPED_ERROR = "skipped_error"
    SKIPPED_LIMIT = "skipped_limit"


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED_HITL = "paused_hitl"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# --- Core models ---


class Block(BaseModel):
    block_id: str
    source_id: str
    source_format: SourceFormat
    block_type: BlockType
    text: str
    order: int
    page_or_slide: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentIR(BaseModel):
    source_id: str
    source_format: SourceFormat
    filename: str
    blocks: list[Block]
    char_count: int
    block_count: int
    warnings: list[str] = Field(default_factory=list)


class PyramidSection(BaseModel):
    level: int
    title: str
    bullets: list[str] = Field(default_factory=list)


class ArticlePlan(BaseModel):
    title: str
    subtitle: str = ""
    audience: str = ""
    thesis: str = ""
    pyramid_outline: list[PyramidSection] = Field(default_factory=list)
    image_prompts: list[str] = Field(default_factory=list)
    estimated_word_count: int = 0
    seo_title: str = ""
    seo_description: str = ""
    tags: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    finding_id: str
    reviewer: ReviewerRole
    severity: Severity
    problem: str
    suggested_fix: str
    block_refs: list[str] = Field(default_factory=list)
    resolved: bool = False
    # Stamp so supervisor ignores leftover items in the append-only new_findings reducer.
    review_iteration: int = 0

    @field_validator("block_refs", mode="before")
    @classmethod
    def coerce_block_refs(cls, value: Any) -> list[str]:
        """Reviewers often return page/block numbers as ints."""
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        return [str(item) for item in value if item is not None and str(item).strip() != ""]


class ImageAsset(BaseModel):
    image_id: str
    prompt: str
    url: str = ""
    local_path: str = ""
    caption: str = ""
    status: ImageStatus = ImageStatus.PENDING
    aspect_ratio: str = "16:9"
    review_passed: bool = True
    review_notes: str = ""
    redraw_prompt: str = ""


class QuizItem(BaseModel):
    question_id: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str = ""


class IterationSnapshot(BaseModel):
    iteration: int = 0
    phase: str = "review"
    summary: str = ""
    markdown: str = ""
    excerpt: str = ""
    word_count: int = 0
    char_count: int = 0
    open_findings_count: int = 0
    findings: list[Finding] = Field(default_factory=list)
    findings_by_reviewer: dict[str, int] = Field(default_factory=dict)
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utc_now_iso)


class NodeEvent(BaseModel):
    node: str
    message: str = ""
    iteration: int = 0
    timestamp: str = Field(default_factory=utc_now_iso)
    level: str = "info"


class LogEntry(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    node: str
    level: LogLevel = LogLevel.INFO
    message: str
    iteration: int = 0
    trace_url: str = ""


class ExportArtifacts(BaseModel):
    markdown: str = ""
    html: str = ""
    clipboard_text: str = ""
    export_path: str = ""


class HumanFeedback(BaseModel):
    approved: bool = False
    change_notes: str = ""


class WebSnippet(BaseModel):
    query: str
    title: str = ""
    url: str = ""
    snippet: str = ""


class WebResearch(BaseModel):
    enabled: bool = False
    queries: list[str] = Field(default_factory=list)
    snippets: list[WebSnippet] = Field(default_factory=list)

    def as_text(self, max_chars: int = 4000) -> str:
        if not self.snippets:
            return ""
        parts: list[str] = []
        for item in self.snippets:
            parts.append(f"- {item.title} ({item.url})\n  {item.snippet}")
        text = "\n".join(parts)
        return text[:max_chars]


# --- LangGraph state ---


class AgentState(TypedDict, total=False):
    run_id: str
    status: PipelineStatus

    # Inputs
    uploaded_files: list[dict[str, Any]]
    skills_rules: str
    skills_compact: str
    topic_hint: str
    enable_web_research: bool

    # Parsed IR
    documents: list[DocumentIR]
    combined_text: str
    parse_report: dict[str, Any]
    skills_audit: dict[str, Any]
    web_research: WebResearch | None

    # Planning & draft
    plan: ArticlePlan | None
    draft_markdown: str
    images: list[ImageAsset]
    image_redraw_count: int

    # Review loop
    iteration: int
    open_findings: list[Finding]
    resolved_findings: list[Finding]
    new_findings: Annotated[list[Finding], operator.add]
    processed_finding_ids: list[str]
    converged: bool
    cap_hit_with_open_findings: bool
    # Consecutive passes that resolved nothing while the rewrite stopped changing the draft.
    stall_count: int
    stalled: bool
    accepted_findings: list[Finding]
    iteration_history: Annotated[list[IterationSnapshot], operator.add]
    node_events: Annotated[list[NodeEvent], operator.add]

    # Editor score gate (1–10), separate from specialist findings
    editor_score: float
    editor_notes: str
    editor_retries: int
    editor_loop: bool

    # Style terminal stage
    style_pass_count: int
    grounding_recheck_count: int
    final_markdown: str

    # Quiz & HITL
    quiz: list[QuizItem]
    human_feedback: HumanFeedback | None

    # Export
    export: ExportArtifacts | None

    # Live UI cursor. Written as soon as a node starts, not when it returns.
    current_node: str
    progress_hint: str
    progress_at: str

    # Observability — reducer append
    logs: Annotated[list[LogEntry], operator.add]
