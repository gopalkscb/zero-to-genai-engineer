"""
Self-Correcting Agentic RAG -- the exact LangGraph built in Notebook 03, saved as an
importable module so both the notebook and the Streamlit app (app.py) share one graph
instead of drifting apart.

Reuses Module 10's HybridIndex, Reranker, and prompts (rag_pipeline.py) UNMODIFIED. This
module's only job is the control flow a straight-line chain can't express: retrying a weak
retrieval, retrying an ungrounded generation, and pausing for a human when both retries are
exhausted.

Graph:
    condense -> retrieve -> grade_documents --sufficient--> generate -> check_groundedness
                    ^             |                             ^            |
                    |        insufficient                       |      not grounded
                    |        (retries left)                 regenerate   (retries left)
                    |             v                              |           v
                    +------ rewrite_query                        +----- regenerate_bump
                                  |
                         (retries exhausted, either check)
                                  v
                           human_escalation --interrupt()--> finalize -> END
"""

import sys
from pathlib import Path
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

RAG_PIPELINE_DIR = Path(__file__).resolve().parents[2] / "10_RAG" / "notebooks" / "production_rag_chatbot"
sys.path.insert(0, str(RAG_PIPELINE_DIR))

from rag_pipeline import (  # noqa: E402
    HybridIndex, Reranker, load_document, chunk_documents,
    format_sources, ANSWER_PROMPT, CONDENSE_PROMPT,
)

MAX_REWRITES = 2
MAX_REGENERATE = 1

GRADE_PROMPT = """Are the SOURCES below sufficient to answer the QUESTION well? Answer with
exactly one word: SUFFICIENT or INSUFFICIENT.

QUESTION: {question}

SOURCES:
{sources}"""

REWRITE_PROMPT = """The QUESTION below did not retrieve sufficient sources from the knowledge
base. Rewrite it to be more specific and retrieval-friendly. Return ONLY the rewritten
question, nothing else.

QUESTION: {question}"""

GROUNDEDNESS_PROMPT = """Does the ANSWER rely ONLY on facts present in the SOURCES, with no
invented details? Answer with exactly one word: GROUNDED or NOT_GROUNDED.

SOURCES:
{sources}

ANSWER:
{answer}"""


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    standalone_question: str
    reranked: list
    grade: str
    rewrite_count: int
    answer: str
    groundedness: str
    regenerate_count: int


def build_graph(model: str = "gpt-4o-mini", data_dir: Path | None = None):
    """Build and compile the Self-Correcting Agentic RAG graph.

    `data_dir` should contain the file(s) to index; if omitted, falls back to Module 10's
    sample_report.pdf so the graph is runnable with zero setup.
    """
    llm = ChatOpenAI(model=model, temperature=0)

    index = HybridIndex()
    reranker = Reranker()

    def ingest(file_paths: list[str]) -> dict:
        pages = []
        for path in file_paths:
            pages.extend(load_document(path))
        chunks = chunk_documents(pages, chunk_size=500, chunk_overlap=80)
        index.build(chunks)
        return {"files": len(file_paths), "pages": len(pages), "chunks": len(chunks)}

    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[2] / "10_RAG" / "notebooks" / "data"
    sample = data_dir / "sample_report.pdf"
    if sample.exists():
        ingest([str(sample)])

    # ---- Nodes --------------------------------------------------------
    def condense(state: AgentState) -> dict:
        question = state["messages"][-1].content
        history = state["messages"][:-1]
        if not history:
            standalone = question
        else:
            history_text = "\n".join(f"{m.type}: {m.content}" for m in history[-6:])
            standalone = llm.invoke(
                CONDENSE_PROMPT.format(history=history_text, question=question)
            ).content.strip()
        return {"standalone_question": standalone, "rewrite_count": 0, "regenerate_count": 0}

    def retrieve(state: AgentState) -> dict:
        candidates = index.search(state["standalone_question"], k=8)
        reranked = reranker.rerank(state["standalone_question"], candidates, top_n=4)
        return {"reranked": reranked}

    def grade_documents(state: AgentState) -> dict:
        sources = format_sources(state["reranked"]) if state["reranked"] else "(nothing retrieved)"
        verdict = llm.invoke(
            GRADE_PROMPT.format(question=state["standalone_question"], sources=sources)
        ).content.strip().upper()
        grade = "insufficient" if "INSUFFICIENT" in verdict else "sufficient"
        return {"grade": grade}

    def rewrite_query(state: AgentState) -> dict:
        rewritten = llm.invoke(REWRITE_PROMPT.format(question=state["standalone_question"])).content.strip()
        return {"standalone_question": rewritten, "rewrite_count": state.get("rewrite_count", 0) + 1}

    def generate(state: AgentState) -> dict:
        history_text = "\n".join(f"{m.type}: {m.content}" for m in state["messages"][:-1][-6:])
        prompt = ANSWER_PROMPT.format(
            sources=format_sources(state["reranked"]), history=history_text,
            question=state["standalone_question"],
        )
        answer = llm.invoke(prompt).content.strip()
        return {"answer": answer}

    def check_groundedness(state: AgentState) -> dict:
        verdict = llm.invoke(
            GROUNDEDNESS_PROMPT.format(sources=format_sources(state["reranked"]), answer=state["answer"])
        ).content.strip().upper()
        groundedness = "not_grounded" if "NOT_GROUNDED" in verdict else "grounded"
        return {"groundedness": groundedness}

    def regenerate_bump(state: AgentState) -> dict:
        return {"regenerate_count": state.get("regenerate_count", 0) + 1}

    def human_escalation(state: AgentState) -> dict:
        guidance = interrupt({
            "reason": "Could not retrieve/generate a grounded answer after retrying.",
            "question": state["standalone_question"],
            "best_effort_answer": state.get("answer"),
            "rewrite_count": state.get("rewrite_count", 0),
            "regenerate_count": state.get("regenerate_count", 0),
        })
        if guidance and guidance.get("human_answer"):
            return {"answer": guidance["human_answer"], "groundedness": "human_provided"}
        return {
            "answer": "I don't have enough grounded information in this document to answer "
                       "confidently, and no human guidance was provided.",
            "groundedness": "refused",
        }

    def finalize(state: AgentState) -> dict:
        return {"messages": [AIMessage(content=state["answer"])]}

    # ---- Routers --------------------------------------------------------
    def route_after_grade(state: AgentState) -> str:
        if state["grade"] == "sufficient":
            return "generate"
        if state.get("rewrite_count", 0) < MAX_REWRITES:
            return "rewrite_query"
        return "human_escalation"

    def route_after_groundedness(state: AgentState) -> str:
        if state["groundedness"] == "grounded":
            return "finalize"
        if state.get("regenerate_count", 0) < MAX_REGENERATE:
            return "regenerate_bump"
        return "human_escalation"

    # ---- Wire the graph --------------------------------------------------------
    builder = StateGraph(AgentState)
    for name, fn in [
        ("condense", condense), ("retrieve", retrieve), ("grade_documents", grade_documents),
        ("rewrite_query", rewrite_query), ("generate", generate),
        ("check_groundedness", check_groundedness), ("regenerate_bump", regenerate_bump),
        ("human_escalation", human_escalation), ("finalize", finalize),
    ]:
        builder.add_node(name, fn)

    builder.add_edge(START, "condense")
    builder.add_edge("condense", "retrieve")
    builder.add_edge("retrieve", "grade_documents")
    builder.add_conditional_edges("grade_documents", route_after_grade, {
        "generate": "generate", "rewrite_query": "rewrite_query", "human_escalation": "human_escalation",
    })
    builder.add_edge("rewrite_query", "retrieve")
    builder.add_edge("generate", "check_groundedness")
    builder.add_conditional_edges("check_groundedness", route_after_groundedness, {
        "finalize": "finalize", "regenerate_bump": "regenerate_bump", "human_escalation": "human_escalation",
    })
    builder.add_edge("regenerate_bump", "generate")
    builder.add_edge("human_escalation", "finalize")
    builder.add_edge("finalize", END)

    graph = builder.compile(checkpointer=InMemorySaver())
    return graph, index, reranker, ingest
