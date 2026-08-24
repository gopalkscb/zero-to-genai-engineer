"""Title and dek polish. Medium readers decide in the first two lines."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.graph.prompt_context import skills_block
from app.graph.state import AgentState, ArticlePlan, LogEntry, LogLevel
from app.graph.trace import make_snapshot
from app.llm.client import LLMClient


class HeadlineOutput(BaseModel):
    title: str = ""
    subtitle: str = ""
    dek: str = Field(default="", description="One-sentence standfirst under the title.")


_H1 = re.compile(r"^#\s+(.+)$", re.M)


def apply_headline(markdown: str, title: str, subtitle: str, dek: str) -> str:
    text = markdown or ""
    title = (title or "").strip()
    subtitle = (subtitle or "").strip()
    dek = (dek or "").strip()
    if not title:
        return text
    if _H1.search(text):
        text = _H1.sub(f"# {title}", text, count=1)
    else:
        text = f"# {title}\n\n{text.lstrip()}"
    # Insert subtitle + dek once, after the H1, if they are not already sitting there.
    lines = text.split("\n")
    h1_at = next((i for i, line in enumerate(lines) if line.startswith("# ")), 0)
    insert: list[str] = []
    rest = lines[h1_at + 1 :]
    rest_joined = "\n".join(rest).lstrip()
    if subtitle and subtitle.lower() not in rest_joined[:400].lower():
        insert.append(f"*{subtitle}*")
    if dek and dek.lower() not in rest_joined[:500].lower():
        if insert:
            insert.append("")
        insert.append(dek)
    if not insert:
        return text
    return "\n".join([lines[h1_at], "", *insert, "", rest_joined]).strip() + "\n"


def headline_node(state: AgentState) -> dict:
    llm = LLMClient()
    draft = state.get("draft_markdown") or ""
    plan = state.get("plan")
    current_title = ""
    current_sub = ""
    if plan is not None:
        current_title = getattr(plan, "title", None) or (plan.get("title") if isinstance(plan, dict) else "") or ""
        current_sub = (
            getattr(plan, "subtitle", None) or (plan.get("subtitle") if isinstance(plan, dict) else "") or ""
        )
    match = _H1.search(draft)
    if match and not current_title:
        current_title = match.group(1).strip()

    prompt = f"""Write a Medium-ready title, subtitle, and one-sentence dek for this article.

House skill:
{skills_block(state)}

Rules:
- Title: under 60 characters, keyword-front-loaded, specific, no trailing period.
- Subtitle: under 150 characters, names the payoff, does not repeat the title.
- Dek: one sentence a skimmer can read under the title. No em dashes.
- Do not invent facts that are not in the draft.

Current title: {current_title}
Current subtitle: {current_sub}

Opening of the article:
{draft[:2500]}"""

    messages = [
        {"role": "system", "content": "You write publication titles. Specific beats clever."},
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.complete("headline", messages, structured_schema=HeadlineOutput, temperature=0.4)
        assert isinstance(result, HeadlineOutput)
    except Exception:
        result = HeadlineOutput(title=current_title, subtitle=current_sub, dek="")

    title = (result.title or current_title).strip()
    subtitle = (result.subtitle or current_sub).strip()
    revised = apply_headline(draft, title, subtitle, result.dek)
    updates: dict = {
        "draft_markdown": revised,
        "iteration_history": [
            make_snapshot(
                iteration=state.get("iteration", 0),
                phase="headline",
                markdown=revised,
                summary=f"Headline: {title}",
            )
        ],
        "logs": [
            LogEntry(
                node="headline",
                level=LogLevel.INFO,
                message=f"Headline set: {title}",
            )
        ],
    }
    if isinstance(plan, ArticlePlan):
        updates["plan"] = plan.model_copy(update={"title": title, "subtitle": subtitle})
    elif isinstance(plan, dict):
        updates["plan"] = {**plan, "title": title, "subtitle": subtitle}
    return updates
