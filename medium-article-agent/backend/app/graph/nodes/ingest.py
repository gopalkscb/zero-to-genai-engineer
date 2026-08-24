"""Ingest node: parse uploads and load the Medium house skill."""

from __future__ import annotations

from app.config import get_settings
from app.editorial.skills import compact_skills
from app.graph.state import AgentState, LogEntry, LogLevel, PipelineStatus
from app.parsing import parse_upload
from app.parsing.normalize import combine_text, normalize_documents, summarize_documents
from app.parsing.source_pack import pack_source


def ingest_node(state: AgentState) -> dict:
    settings = get_settings()
    run_id = state.get("run_id", "unknown")
    uploaded = state.get("uploaded_files", [])

    logs: list[LogEntry] = [
        LogEntry(node="ingest", level=LogLevel.INFO, message=f"Ingesting {len(uploaded)} file(s)")
    ]

    skills_rules = settings.load_style_guide()
    skills_compact = compact_skills(skills_rules)
    logs.append(
        LogEntry(
            node="ingest",
            level=LogLevel.INFO,
            message=f"Style guide loaded ({len(skills_rules)} chars; compact checklist {len(skills_compact)} chars)",
        )
    )

    documents = []
    for idx, item in enumerate(uploaded):
        content = item.get("content", b"")
        filename = item.get("filename", f"file_{idx}")
        source_id = item.get("source_id", f"src{idx + 1}")
        doc = parse_upload(content, filename, source_id)
        documents.append(doc)
        warn = f", {len(doc.warnings)} warning(s)" if doc.warnings else ""
        logs.append(
            LogEntry(
                node="ingest",
                level=LogLevel.WARNING if doc.warnings else LogLevel.INFO,
                message=f"Parsed {filename}: {doc.block_count} blocks, {doc.char_count} chars{warn}",
            )
        )

    documents = normalize_documents(documents)
    combined = combine_text(documents)
    parse_report = summarize_documents(documents)
    packed = pack_source(documents, combined, budget=28000)
    parse_report["packed"] = len(packed) < len(combined)
    parse_report["prompt_chars"] = len(packed)

    if parse_report["packed"]:
        logs.append(
            LogEntry(
                node="ingest",
                level=LogLevel.WARNING,
                message=(
                    f"Sources are {len(combined)} chars. Prompts will use a coverage pack "
                    f"({len(packed)} chars) that keeps every heading, table, and code block."
                ),
            )
        )

    return {
        "run_id": run_id,
        "status": PipelineStatus.RUNNING,
        "skills_rules": skills_rules,
        "skills_compact": skills_compact,
        "documents": documents,
        "combined_text": combined,
        "parse_report": parse_report,
        "iteration": 0,
        "open_findings": [],
        "resolved_findings": [],
        "new_findings": [],
        "processed_finding_ids": [],
        "converged": False,
        "cap_hit_with_open_findings": False,
        "stalled": False,
        "stall_count": 0,
        "image_redraw_count": 0,
        "editor_score": 0.0,
        "editor_notes": "",
        "editor_retries": 0,
        "editor_loop": False,
        "style_pass_count": 0,
        "grounding_recheck_count": 0,
        "logs": logs,
    }
