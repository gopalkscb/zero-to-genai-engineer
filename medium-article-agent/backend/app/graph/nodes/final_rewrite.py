"""Final rewrite — last polish + em dash strip."""

from __future__ import annotations

from app.editorial.skills import apply_deterministic_fixes, lint_article
from app.graph.prompt_context import skills_block
from app.graph.state import AgentState, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient
from app.utils.dash_check import assert_no_em_en_dash, strip_em_en_dashes


def final_rewrite_node(state: AgentState) -> dict:
    llm = LLMClient()
    draft = state.get("draft_markdown", "")
    skills = skills_block(state)
    dash_retries = state.get("dash_retry_count", 0)

    prompt = f"""Final polish pass for Medium publication.
House skill:
{skills}

CRITICAL: Do NOT use em dashes (—) or en dashes (–). Use commas, periods, or hyphens.
Keep every Markdown image exactly as written, including the italic caption line after it.
Do not replace images with example.com placeholders.
Do not shorten the piece or delete the worked example, definitions, or numbers.
Keep the AI disclosure as the last line.
Do not wrap the article in a markdown code fence. Return the Markdown body only.

Draft:
{draft}

Return the final publication-ready Markdown."""

    messages = [
        {"role": "system", "content": "You are a final Medium editor."},
        {"role": "user", "content": prompt},
    ]
    final = llm.complete("final", messages, temperature=0.4)
    assert isinstance(final, str)
    final = apply_deterministic_fixes(final)

    violations = assert_no_em_en_dash(final)
    if violations:
        final = strip_em_en_dashes(final)
        violations = assert_no_em_en_dash(final)

    audit = lint_article(final, skills_rules=state.get("skills_rules") or "", images=state.get("images") or [])
    failed = [item.check_id for item in audit.checks if not item.passed]

    logs = [
        LogEntry(
            node="final_rewrite",
            level=LogLevel.INFO,
            message=f"Final rewrite complete ({len(final)} chars)",
        )
    ]
    if violations:
        logs.append(
            LogEntry(
                node="final_rewrite",
                level=LogLevel.WARNING,
                message=f"Em/en dash violations remain after strip: {len(violations)}",
            )
        )

    if failed:
        logs.append(
            LogEntry(
                node="final_rewrite",
                level=LogLevel.WARNING,
                message=f"House skill still open after deterministic fixes: {', '.join(failed)}",
            )
        )

    return {
        "final_markdown": final,
        "draft_markdown": final,
        "skills_audit": audit.as_dict(),
        "dash_retry_count": dash_retries + (1 if violations else 0),
        "iteration_history": [
            make_snapshot(
                iteration=state.get("iteration", 0),
                phase="final",
                markdown=final,
                summary=f"Final rewrite complete ({len(final)} chars)",
            )
        ],
        "logs": logs,
    }
