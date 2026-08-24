"""Shared prompt context: full house skill + coverage-preserving source pack."""

from __future__ import annotations

from app.editorial.skills import compact_skills
from app.graph.state import AgentState
from app.parsing.source_pack import pack_source

PLAN_SOURCE_BUDGET = 20000
DRAFT_SOURCE_BUDGET = 28000
REVIEW_SOURCE_BUDGET = 8000
GROUNDING_SOURCE_BUDGET = 14000
EDITOR_SOURCE_BUDGET = 10000
REWRITE_SOURCE_BUDGET = 8000


def skills_block(state: AgentState, *, full: bool = False) -> str:
    compact = state.get("skills_compact") or compact_skills(state.get("skills_rules") or "")
    if not full:
        return compact
    guide = state.get("skills_rules") or compact
    if not guide:
        return compact
    if compact and compact != guide:
        return f"{compact}\n\n---\nFull house skill from backend/skills/medium.md:\n{guide}"
    return guide


def source_block(state: AgentState, budget: int = DRAFT_SOURCE_BUDGET) -> str:
    return pack_source(state.get("documents") or [], state.get("combined_text") or "", budget=budget)
