"""Style pass node — humanization before final rewrite."""

from __future__ import annotations

from app.config import get_settings
from app.graph.prompt_context import skills_block
from app.graph.state import AgentState, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient


def style_pass_node(state: AgentState) -> dict:
    settings = get_settings()
    count = state.get("style_pass_count", 0) + 1
    if count > settings.max_style_pass:
        return {
            "logs": [
                LogEntry(
                    node="style_pass",
                    level=LogLevel.WARNING,
                    message="Style pass cap reached — proceeding",
                )
            ]
        }

    llm = LLMClient()
    draft = state.get("draft_markdown", "")
    skills = skills_block(state)

    prompt = f"""Apply Medium style humanization to this draft.
House skill:
{skills}

Rules:
- NO em dashes, NO en dashes. Use commas or periods.
- Zero banned AI-isms from the house skill.
- Make it conversational and engaging.
- Do not shorten the article. Keep every definition, worked example, number, and citation.
- Keep every Markdown image URL and italic caption byte for byte.
- Keep the AI disclosure at the bottom.
- Max 3 sentences per paragraph. At least 3 bold golden sentences.
- Do not wrap the article in a markdown code fence.

Draft:
{draft}

Return the full improved draft in Markdown."""

    messages = [
        {"role": "system", "content": "You are a Medium style editor."},
        {"role": "user", "content": prompt},
    ]
    styled = llm.complete("style", messages, temperature=0.6)
    assert isinstance(styled, str)

    return {
        "draft_markdown": styled,
        "style_pass_count": count,
        "iteration_history": [
            make_snapshot(
                iteration=state.get("iteration", 0),
                phase="style",
                markdown=styled,
                summary=f"Style pass {count} complete",
            )
        ],
        "logs": [
            LogEntry(
                node="style_pass",
                level=LogLevel.INFO,
                message=f"Style pass {count} complete",
            )
        ],
    }
