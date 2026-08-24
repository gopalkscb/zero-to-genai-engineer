"""Rewrite node — fix every carried-forward finding, critical→major→minor."""

from __future__ import annotations

from app.graph.runtime import report
from app.graph.state import AgentState, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.graph.nodes.supervisor import sort_findings_by_severity
from app.graph.prompt_context import REWRITE_SOURCE_BUDGET, skills_block, source_block
from app.llm.client import LLMClient


def format_findings_for_rewrite(findings) -> str:
    lines: list[str] = []
    for item in findings:
        lines.append(
            f"- ID {item.finding_id} [{item.severity.value}] ({item.reviewer.value})\n"
            f"  Problem: {item.problem}\n"
            f"  Required fix: {item.suggested_fix}"
        )
    return "\n".join(lines)


def rewrite_node(state: AgentState) -> dict:
    run_id = str(state.get("run_id") or "unknown")
    llm = LLMClient()
    draft = state.get("draft_markdown", "")
    open_findings = sort_findings_by_severity(
        [item for item in state.get("open_findings", []) if not getattr(item, "resolved", False)]
    )
    iteration = state.get("iteration", 0) + 1
    logs = [
        report(
            run_id,
            "rewrite",
            f"Rewriting iteration {iteration} from {len(open_findings)} open finding(s). This can take a minute.",
        )
    ]
    findings_text = format_findings_for_rewrite(open_findings) or "- None"
    skills = skills_block(state)
    source = source_block(state, REWRITE_SOURCE_BUDGET)

    prompt = f"""Rewrite this Medium article so EVERY listed finding is actually fixed.
These findings were left open from the previous review. Do not ignore any of them.
Priority: critical first, then major, then minor.

House skill (must still pass after the rewrite):
{skills}

How to fix, not how to dodge:
- If a finding says a definition is missing, write the definition in the opening.
- If a finding says an acronym is unexplained, expand it on first use.
- If a finding says there is no worked example, add one with actual steps or numbers from the source pack.
- If a finding asks for a citation, ground the claim in the source material already in the draft.
- If a finding is a house-skill miss (banned phrase, disclosure, word count, H2s), fix that exactly.
- Do not "fix" a missing section by adding one vague sentence. Add the real section.

Keep the article at least as long as it is now, and aim for 1200-1500 words.
Do NOT use em dashes or en dashes.
Keep every Markdown image at its current position with its italic caption, and keep the
image URL byte for byte. You may edit the alt text inside the square brackets when a
finding asks for it.
Do not wrap the article in a markdown code fence.
If a finding is already satisfied by the current draft, leave that part alone rather than
rewording it, so the reviewers can see the fix survived.
End with the AI disclosure if it is missing.

Open findings ({len(open_findings)}):
{findings_text}

Source pack (use named facts if a finding needs them):
{source}

Current draft:
{draft}

Return the complete rewritten draft in Markdown only."""

    messages = [
        {"role": "system", "content": "You are an expert Medium editor. You close review findings, you do not skip them."},
        {"role": "user", "content": prompt},
    ]
    revised = llm.complete("rewrite", messages, temperature=0.3)
    assert isinstance(revised, str)

    return {
        "draft_markdown": revised,
        "iteration": iteration,
        # Keep the same open findings so reviewers must verdict them. Do not wipe the list.
        "open_findings": open_findings,
        "iteration_history": [
            make_snapshot(
                iteration=iteration,
                phase="rewrite",
                markdown=revised,
                findings=open_findings,
                summary=f"Rewrite {iteration} addressed {len(open_findings)} carried finding(s)",
            )
        ],
        "logs": logs
        + [
            LogEntry(
                node="rewrite",
                level=LogLevel.INFO,
                message=f"Rewrite iteration {iteration} received {len(open_findings)} finding(s) to fix",
                iteration=iteration,
            )
        ],
    }
