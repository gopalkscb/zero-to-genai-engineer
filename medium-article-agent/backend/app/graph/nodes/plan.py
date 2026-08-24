"""Plan node — generate ArticlePlan from IR."""

from __future__ import annotations

from app.config import get_settings
from app.graph.prompt_context import PLAN_SOURCE_BUDGET, skills_block, source_block
from app.graph.runtime import report
from app.graph.state import AgentState, ArticlePlan, LogEntry, LogLevel
from app.llm.client import LLMClient
from app.llm.prompts import render_prompt


def plan_node(state: AgentState) -> dict:
    run_id = str(state.get("run_id") or "unknown")
    logs = [report(run_id, "plan", "Planning the article. This LLM call can take a minute.")]
    settings = get_settings()
    llm = LLMClient(settings)
    prompt = render_prompt(
        "plan.j2",
        skills_rules=state.get("skills_rules", ""),
        skills_compact=skills_block(state),
        topic_hint=state.get("topic_hint", ""),
        source_pack=source_block(state, PLAN_SOURCE_BUDGET),
        image_count=settings.image_count,
    )
    messages = [
        {"role": "system", "content": "You are an expert Medium editorial planner."},
        {"role": "user", "content": prompt},
    ]
    plan = llm.complete("plan", messages, structured_schema=ArticlePlan, temperature=0.5)
    assert isinstance(plan, ArticlePlan)

    return {
        "plan": plan,
        "current_node": "plan",
        "logs": logs
        + [
            LogEntry(
                node="plan",
                level=LogLevel.INFO,
                message=f"Plan created: '{plan.title}' with {len(plan.pyramid_outline)} sections",
            )
        ],
    }
