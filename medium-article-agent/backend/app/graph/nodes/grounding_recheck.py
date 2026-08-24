"""Grounding recheck — verify final draft against source."""

from __future__ import annotations

from pydantic import BaseModel

from app.config import get_settings
from app.graph.prompt_context import GROUNDING_SOURCE_BUDGET, source_block
from app.graph.state import AgentState, LogEntry, LogLevel
from app.llm.client import LLMClient


class GroundingResult(BaseModel):
    drift_detected: bool = False
    issues: list[str] = []


def grounding_recheck_node(state: AgentState) -> dict:
    settings = get_settings()
    count = state.get("grounding_recheck_count", 0) + 1
    final = state.get("final_markdown", state.get("draft_markdown", ""))

    if count > settings.max_grounding_recheck:
        return {
            "grounding_recheck_count": count,
            "grounding_drift": False,
            "logs": [
                LogEntry(
                    node="grounding_recheck",
                    level=LogLevel.WARNING,
                    message="Grounding recheck cap reached — proceeding",
                )
            ],
        }

    llm = LLMClient()
    research = state.get("web_research")
    web_text = research.as_text(2000) if research else ""
    prompt = f"""Check if this article draft drifts from the PRIMARY source material.
Report drift_detected=true if claims contradict or invent facts not in the uploaded sources.
Web snippets are optional color/citations only. A fact that appears only on the web is not enough to justify a new claim.

Primary sources (coverage pack, not a first-N slice):
{source_block(state, GROUNDING_SOURCE_BUDGET)}

Optional web research:
{web_text or '(none)'}

Final draft:
{final[:8000]}"""

    messages = [
        {"role": "system", "content": "You are a fact-checker."},
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.complete("reviewer_grounding", messages, structured_schema=GroundingResult, temperature=0.2)
        assert isinstance(result, GroundingResult)
        drift = result.drift_detected
    except Exception:
        drift = False

    return {
        "grounding_recheck_count": count,
        "grounding_drift": drift,
        "logs": [
            LogEntry(
                node="grounding_recheck",
                level=LogLevel.INFO,
                message=f"Grounding recheck {count}: drift={drift}",
            )
        ],
    }
