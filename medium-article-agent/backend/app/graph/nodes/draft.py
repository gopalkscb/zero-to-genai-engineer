"""Draft node — generate markdown article from plan."""

from __future__ import annotations

from app.config import get_settings
from app.graph.prompt_context import DRAFT_SOURCE_BUDGET, skills_block, source_block
from app.graph.runtime import report
from app.graph.state import AgentState, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient
from app.llm.prompts import render_prompt


def draft_node(state: AgentState) -> dict:
    run_id = str(state.get("run_id") or "unknown")
    logs = [report(run_id, "draft", "Writing the first draft. This LLM call can take a minute.")]
    settings = get_settings()
    llm = LLMClient(settings)
    plan = state.get("plan")
    if not plan:
        return {
            "logs": logs
            + [
                LogEntry(node="draft", level=LogLevel.ERROR, message="No plan available")
            ]
        }

    research = state.get("web_research")
    web_research_text = research.as_text() if research else ""
    prompt = render_prompt(
        "draft.j2",
        skills_rules=state.get("skills_rules", ""),
        skills_compact=skills_block(state),
        plan=plan,
        source_pack=source_block(state, DRAFT_SOURCE_BUDGET),
        web_research_text=web_research_text,
    )
    messages = [
        {"role": "system", "content": "You are an expert Medium writer. You follow the house skill as law."},
        {"role": "user", "content": prompt},
    ]
    draft = llm.complete("draft", messages, temperature=0.55)
    assert isinstance(draft, str)

    return {
        "draft_markdown": draft,
        "current_node": "draft",
        "iteration_history": [
            make_snapshot(
                iteration=0,
                phase="draft",
                markdown=draft,
                summary=f"First draft generated ({len(draft)} chars)",
            )
        ],
        "logs": logs
        + [
            LogEntry(
                node="draft",
                level=LogLevel.INFO,
                message=f"Draft generated ({len(draft)} chars)",
            )
        ],
    }
