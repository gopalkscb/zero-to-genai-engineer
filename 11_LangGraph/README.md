# Session 11 — LangGraph (Stateful Agents)
### M10 — Complete

> **What was MISSING from S10:** Module 10 built a genuinely production-grade RAG pipeline —
> hybrid retrieval, reranking, a groundedness guardrail, conversational memory — but
> `ProductionRAGChatbot.chat()` is a **straight line**: retrieve → rerank → guardrail →
> generate, every time, no matter what. It can't retry a bad retrieval, can't rewrite a vague
> question, can't pause and ask a human when it's genuinely stuck, and its "memory" is a
> Python list living inside one process. LangGraph is the fix: it turns that straight line
> into a **graph with cycles, persistent state, and a pause button** — which is exactly what
> "agent" means once you stop hand-waving the word.

---

## What This Session Covers

| Day | Topic | Key Concepts |
|-----|-------|--------------|
| S11a | LangGraph Fundamentals & Agents | `StateGraph`, nodes, edges, conditional routing, `add_messages` reducer, tool-calling agents (`ToolNode`, `create_agent`), checkpointer memory, streaming |
| S11b | Human-in-the-Loop & Multi-Agent | `interrupt()` / `Command(resume=...)`, long-term memory (`Store`), supervisor pattern with `Command(goto=...)` handoffs |
| S11c | Capstone — Agentic RAG | Every Module 10 building block (hybrid search, rerank, groundedness) reused inside a self-correcting LangGraph agent: query rewriting, retrieval grading, hallucination checks, human escalation |

---

## Contents

| File | Description |
|------|--------------|
| `notebooks/01_langgraph_fundamentals_and_agents.ipynb` | Graphs, state, conditional edges, tool-calling agents, memory, streaming |
| `notebooks/02_human_in_the_loop_and_multi_agent.ipynb` | `interrupt()`-based approval flows, long-term memory, supervisor multi-agent pattern |
| `notebooks/03_agentic_rag_capstone.ipynb` | **Flagship project** — Self-Correcting Agentic RAG, built on top of the Module 10 pipeline |
| `capstone_agentic_rag/` | The capstone graph exported as a standalone Streamlit app |

---

## Why LangGraph (not just LangChain / LCEL)

An LCEL chain (`prompt \| llm \| parser`) is a **DAG that runs once, forward, and stops.**
That's fine for "retrieve then answer." It falls apart the moment the task needs any of:

- **Loops** — "try again with a better query" (LCEL has no way back to an earlier step)
- **Branching on model output** — "if the answer isn't grounded, regenerate; if it's still
  bad, ask a human" (conditional logic belongs in code, not a pipe chain)
- **Durable, resumable state** — pause mid-task (approval, rate limit, crash) and resume
  *exactly where it left off*, not from the top
- **Multiple cooperating agents** — a supervisor that hands work to specialists and gets
  control back

LangGraph models the whole thing as a **graph**: `State` (a typed, shared scratchpad) flows
through `Nodes` (plain Python functions) connected by `Edges` (including conditional ones
that branch on the current state). A `Checkpointer` snapshots that state after every node,
which is what makes memory, crash-recovery, and human-in-the-loop all the same mechanism
instead of three separate features.

---

## Key Concepts & Latest API (verified against LangChain/LangGraph docs, Aug 2026)

LangChain and LangGraph both shipped **v1.0** in 2026. The headline change: `create_agent`
(in the `langchain` package) is now the recommended way to build a tool-calling agent —
built *on top of* the LangGraph runtime, with a middleware system for customizing the loop.
`create_react_agent` (in `langgraph.prebuilt`) still works but is the legacy prebuilt; we
teach the underlying `StateGraph` mechanics first so students understand what either
high-level API is doing for them, not just how to call it.

| Concept | Import | What it does |
|---|---|---|
| `StateGraph` | `langgraph.graph` | Declares the state schema, then `add_node` / `add_edge` / `add_conditional_edges` / `compile()` |
| `START`, `END` | `langgraph.graph` | Sentinel nodes marking graph entry/exit |
| `MessagesState`, `add_messages` | `langgraph.graph` | Prebuilt chat-history state + reducer that appends instead of overwriting |
| `create_agent` | `langchain.agents` | LangChain 1.0's high-level agent builder — model + tools + middleware, built on `StateGraph` |
| `create_react_agent` | `langgraph.prebuilt` | Legacy prebuilt ReAct agent (still supported; `create_agent` is now recommended for new code) |
| `ToolNode`, `tools_condition` | `langgraph.prebuilt` | Executes tool calls the model requested; routes back to the model or to `END` |
| `Command` | `langgraph.types` | A node's return value that both updates state **and** picks the next node (`goto=`) — this is how multi-agent handoffs work |
| `Send` | `langgraph.types` | Fans one node out into N parallel node executions (map-reduce over a list) |
| `interrupt()` | `langgraph.types` | Pauses the graph mid-node, surfaces a payload to the caller, and waits — the primitive behind every human-in-the-loop pattern |
| `Command(resume=...)` | `langgraph.types` | Resumes a graph paused by `interrupt()`, feeding the human's response back into the exact node that asked |
| `MemorySaver` / `InMemorySaver` | `langgraph.checkpoint.memory` | In-process checkpointer — short-term memory keyed by `thread_id` |
| `Store` (`InMemoryStore`) | `langgraph.store.memory` | Cross-thread, long-term memory (user facts that outlive a single conversation) |
| `graph.stream(..., stream_mode=...)` | — | `"values"` (full state each step), `"updates"` (diff per node), `"messages"` (LLM tokens) |
| `create_supervisor` | `langgraph_supervisor` (companion package) | One-line supervisor multi-agent setup on top of the same `Command(goto=...)` handoff mechanism |

**Sources consulted:**
- [LangChain & LangGraph Reach v1.0](https://www.langchain.com/blog/langchain-langgraph-1dot0)
- [Interrupts — Docs by LangChain](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Making it easier to build human-in-the-loop agents with interrupt](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)
- [create_react_agent reference](https://reference.langchain.com/python/langgraph.prebuilt/chat_agent_executor/create_react_agent)
- [Self-Reflective RAG with LangGraph](https://www.langchain.com/blog/agentic-rag-with-langgraph)
- [Human-in-the-loop — Docs by LangChain](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

Because framework APIs move fast, every notebook's install cell pins nothing tighter than
`langgraph>=0.6` / `langchain>=1.0` and prints the installed version on import — if an
import in these notebooks breaks against a newer release, that printed version number is
the first thing to check.

---

## How to Teach This Effectively — the Plan

**1. Never open with the framework. Open with the pain.**
Re-run `ProductionRAGChatbot.chat()` from Module 10 live, on a question deliberately chosen
to need a second retrieval attempt (too vague the first time). Watch it confidently return
a weak, unguarded answer because it has no way to say "let me try that search again." *That
gap* is the entire motivation for S11 — don't state it, show it.

**2. Build the mental model before the API.**
Draw the graph on a whiteboard/slide before writing code: boxes (nodes) and arrows (edges),
one arrow forking into two with a diamond (conditional edge), one arrow pointing backward
(the loop LCEL couldn't do). Only once students can draw an agent's control flow by hand
should the `StateGraph` API show up — it's then just syntax for a picture they already
understand.

**3. Teach the primitive under every "magic" helper.**
`create_agent` and `create_react_agent` both hide a `StateGraph` with a model node, a tools
node, and a conditional edge between them. Build that graph by hand first (S11a Section 3)
so the prebuilt helpers read as "the same four lines, packaged" instead of a black box.

**4. Make state visible, always.**
After every graph run, print the full state dict and — separately — call
`graph.get_graph().draw_mermaid()` to render the actual graph. Students should never have to
imagine what the graph looks like or what's in state; both are one line of code away, every
single time.

**5. HITL and memory are the payoff, not a bonus topic.**
Don't teach `interrupt()` as an isolated feature. Tie it back to a real failure mode already
established in S10 (Notebook 11 — "human-in-the-loop pauses before anything risky"): the
capstone's `human_escalation` node is the *formal, resumable* version of the ad-hoc pause
that session gestured at. Same for memory — S10's `ChatTurn` list was memory that dies when
the process exits; a `checkpointer` is the same idea made durable and inspectable.

**6. The capstone must extend prior work, not restart from a tutorial.**
The flagship project (`03_agentic_rag_capstone.ipynb`) literally imports
`HybridIndex`, `Reranker`, and the exact prompts from
`10_RAG/notebooks/production_rag_chatbot/rag_pipeline.py`. Nothing about retrieval, fusion,
or reranking is retaught — LangGraph's job in this session is *only* to add what a straight
Python chain structurally cannot: retry loops, self-grading, and a human escape hatch.
Students should leave seeing LangGraph as "the orchestration layer on top of what I already
built," not a separate, disconnected framework.

**7. Assess with a trace, not just a final answer.**
Because state and node transitions are fully inspectable, grade the *path* the agent took —
did it correctly grade a weak retrieval as insufficient? did it rewrite the query sensibly?
did it escalate instead of confidently hallucinating? — not only whether the final answer
looks right. A correct answer reached by skipping the grading step is a bug, not a pass.

---

## Real-World Use Cases for LangGraph (beyond this capstone)

| Use case | Why a graph, not a chain |
|---|---|
| **Customer support triage** | Router node classifies the ticket; billing/technical/refund specialist subgraphs handle it; a supervisor collects and merges results |
| **Code review agent** | Loop: run linter/tests → if failing, ask the model to fix → re-run → stop only when green (the exact "5-step loop pattern" from S09, now as a graph) |
| **Approval-gated automation** (send email, execute a trade, delete a record) | `interrupt()` before the risky tool call; a human approves, edits, or rejects before the graph resumes |
| **Deep research agent** | `Send` fans a topic out into parallel sub-searches; results are reduced back into one report node |
| **Long-running personal assistant** | `Store`-backed long-term memory recalls user preferences across sessions that started days apart |

---

## Capstone — Self-Correcting Agentic RAG

**The pitch:** everything Module 10 taught (hybrid retrieval, RRF fusion, cross-encoder
reranking, a groundedness guardrail, condense-question memory) reused *as-is*, wrapped in a
LangGraph agent that can now do what a straight pipeline never could:

```
        ┌────────────┐
        │  condense  │  (memory-aware question rewrite)
        └─────┬──────┘
              ▼
        ┌────────────┐
   ┌───▶│  retrieve  │  (Module 10's HybridIndex + Reranker, verbatim)
   │    └─────┬──────┘
   │          ▼
   │   ┌───────────────┐   insufficient, retries left
   │   │grade_documents│───────────────────┐
   │   └─────┬─────────┘                   ▼
   │      sufficient              ┌────────────────┐
   │          ▼                   │  rewrite_query │
   │    ┌────────────┐            └───────┬────────┘
   │    │  generate  │◀───────────────────┘
   │    └─────┬──────┘
   │          ▼
   │  ┌───────────────────┐  not grounded, retries left
   │  │ check_groundedness│──────────────────┐
   │  └─────┬─────────────┘                  │
   │     grounded                            ▼
   │        │                    retries exhausted (either check)
   │        ▼                                ▼
   │      END                     ┌────────────────────┐
   └───────────────────────────── │  human_escalation   │
                                   │     interrupt()      │
                                   └──────────┬───────────┘
                                              ▼
                                             END
```

Run it end to end in `notebooks/03_agentic_rag_capstone.ipynb`, then ship it as a chat app
from `capstone_agentic_rag/` (`streamlit run app.py`) — including a live trace panel showing
which nodes fired, how many retries happened, and why (if it happened) the agent handed off
to a human instead of guessing.
