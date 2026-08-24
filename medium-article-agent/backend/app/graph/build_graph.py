"""Build LangGraph — full editorial pipeline."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.config import get_settings
from app.graph.checkpointer import get_checkpointer
from app.graph.nodes.draft import draft_node
from app.graph.nodes.editor_score import editor_score_node, route_after_editor_score
from app.graph.nodes.export import export_node
from app.graph.nodes.final_rewrite import final_rewrite_node
from app.graph.nodes.grounding_recheck import grounding_recheck_node
from app.graph.nodes.headline import headline_node
from app.graph.nodes.human_gate import human_gate_node
from app.graph.nodes.image_gen import image_gen_node
from app.graph.nodes.image_review import (
    image_redraw_node,
    image_review_node,
    images_need_redraw,
)
from app.graph.nodes.ingest import ingest_node
from app.graph.nodes.plan import plan_node
from app.graph.nodes.reviewers import (
    reviewer_grounding_node,
    reviewer_reader_node,
    reviewer_structure_node,
    reviewer_style_node,
    reviewer_technical_node,
)
from app.graph.nodes.rewrite import rewrite_node
from app.graph.nodes.rewrite_voice import rewrite_voice_node
from app.graph.nodes.skills_lint import skills_lint_node
from app.graph.nodes.style_pass import style_pass_node
from app.graph.nodes.supervisor import route_after_supervisor, supervisor_node
from app.graph.nodes.web_research import web_research_node
from app.graph.state import AgentState

REVIEWERS = (
    "reviewer_technical",
    "reviewer_style",
    "reviewer_structure",
    "reviewer_grounding",
    "reviewer_reader",
    "reviewer_skills",
)


def fan_out_reviewers(state: AgentState) -> list[Send]:
    return [Send(name, state) for name in REVIEWERS]


def route_after_image_review(state: AgentState):
    """Redraw rejected figures, else fan out to specialist reviewers + house-skill lint."""
    settings = get_settings()
    used = int(state.get("image_redraw_count") or 0)
    if images_need_redraw(state) and used < int(settings.max_image_redraw):
        return "image_redraw"
    return fan_out_reviewers(state)


def route_after_rewrite_voice(state: AgentState):
    """Editor-injected defects go back to the editor. Specialist findings re-enter review."""
    if state.get("editor_loop"):
        return "editor_score"
    return fan_out_reviewers(state)


def route_after_grounding(state: AgentState) -> str:
    if state.get("grounding_recheck_count", 0) >= 2 and state.get("grounding_drift"):
        return "human_gate"
    if state.get("grounding_drift"):
        return "final_rewrite"
    return "human_gate"


def route_after_human(state: AgentState) -> str:
    feedback = state.get("human_feedback")
    if feedback and not feedback.approved:
        return "rewrite"
    return "export"


def build_graph(*, linear_only: bool = False, checkpointer=None):
    """Build graph. linear_only=True for Phase 2 happy path."""
    builder = StateGraph(AgentState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("plan", plan_node)
    builder.add_node("web_research", web_research_node)
    builder.add_node("draft", draft_node)
    builder.add_node("image_gen", image_gen_node)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "plan")
    builder.add_edge("plan", "web_research")
    builder.add_edge("web_research", "draft")
    builder.add_edge("draft", "image_gen")

    if linear_only:
        builder.add_edge("image_gen", END)
        return builder.compile()

    builder.add_node("image_review", image_review_node)
    builder.add_node("image_redraw", image_redraw_node)
    builder.add_node("reviewer_technical", reviewer_technical_node)
    builder.add_node("reviewer_style", reviewer_style_node)
    builder.add_node("reviewer_structure", reviewer_structure_node)
    builder.add_node("reviewer_grounding", reviewer_grounding_node)
    builder.add_node("reviewer_reader", reviewer_reader_node)
    builder.add_node("reviewer_skills", skills_lint_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("rewrite_voice", rewrite_voice_node)
    builder.add_node("editor_score", editor_score_node)
    builder.add_node("headline", headline_node)
    builder.add_node("style_pass", style_pass_node)
    builder.add_node("final_rewrite", final_rewrite_node)
    builder.add_node("grounding_recheck", grounding_recheck_node)
    builder.add_node("human_gate", human_gate_node)
    builder.add_node("export", export_node)

    builder.add_edge("image_gen", "image_review")
    builder.add_conditional_edges("image_review", route_after_image_review)
    builder.add_edge("image_redraw", "image_review")
    for reviewer in REVIEWERS:
        builder.add_edge(reviewer, "supervisor")

    builder.add_conditional_edges("supervisor", route_after_supervisor)
    builder.add_edge("rewrite", "rewrite_voice")
    builder.add_conditional_edges("rewrite_voice", route_after_rewrite_voice)
    builder.add_conditional_edges("editor_score", route_after_editor_score)
    builder.add_edge("headline", "style_pass")
    builder.add_edge("style_pass", "final_rewrite")
    builder.add_edge("final_rewrite", "grounding_recheck")
    builder.add_conditional_edges("grounding_recheck", route_after_grounding)
    builder.add_conditional_edges("human_gate", route_after_human)
    builder.add_edge("export", END)

    if checkpointer is None:
        checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_gate"])
