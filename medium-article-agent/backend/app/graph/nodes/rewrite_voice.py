"""Second rewrite agent: Medium voice only. Does not change facts or structure.

Production writing graphs split "fix the findings" from "make it readable".
One model doing both tends to shrink the draft or skip a finding while polishing.
"""

from __future__ import annotations

from app.graph.prompt_context import skills_block
from app.graph.state import AgentState, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient


def rewrite_voice_node(state: AgentState) -> dict:
    llm = LLMClient()
    draft = state.get("draft_markdown", "")
    iteration = state.get("iteration", 0)
    open_findings = [item for item in state.get("open_findings", []) if not getattr(item, "resolved", False)]
    skills = skills_block(state)

    prompt = f"""Polish this Medium article for voice and skimability without changing meaning.

House skill:
{skills}

Rules:
- Keep every fact, number, name, definition, worked example, and citation.
- Keep the article at least as long as it is now (1,000–1,500 words).
- Short paragraphs. Max 3 sentences. Subheadings a skimmer can follow.
- First two paragraphs must still define the core term.
- Zero banned AI-isms. No em dashes or en dashes.
- Keep every Markdown image at its current position with its italic caption.
- Keep each image URL byte for byte. You may only edit alt text inside the square brackets.
- Keep the AI disclosure at the bottom.
- Do not wrap the article in a markdown code fence.

Current draft:
{draft}

Return the complete polished draft in Markdown only."""

    messages = [
        {
            "role": "system",
            "content": "You are a Medium copy editor. You polish voice. You never drop facts or shorten the piece.",
        },
        {"role": "user", "content": prompt},
    ]
    revised = llm.complete("rewrite_voice", messages, temperature=0.35)
    assert isinstance(revised, str)

    return {
        "draft_markdown": revised,
        "open_findings": open_findings,
        "iteration_history": [
            make_snapshot(
                iteration=iteration,
                phase="voice",
                markdown=revised,
                findings=open_findings,
                summary=f"Voice pass on rewrite {iteration}",
            )
        ],
        "logs": [
            LogEntry(
                node="rewrite_voice",
                level=LogLevel.INFO,
                message=f"Voice polish after rewrite {iteration} ({len(revised)} chars)",
                iteration=iteration,
            )
        ],
    }
