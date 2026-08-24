# Teaching Session 11 — instructor notes

**Students:** use [`README.md`](README.md). This file is how to *deliver* the session.

---

## How to teach this effectively

**1. Never open with the framework. Open with the pain.**
Re-run `ProductionRAGChatbot.chat()` from Module 10 live, on a question that needs a second retrieval attempt. Watch it return a weak answer because it has no way to say "let me search again." *That gap* is S11.

**2. Build the mental model before the API.**
Draw boxes (nodes) and arrows (edges) — including a backward arrow (the loop LCEL cannot do) — before `StateGraph` appears.

**3. Teach the primitive under every helper.**
`create_agent` / `create_react_agent` hide a model node, a tools node, and a conditional edge. Build that graph by hand in S11a Section 3 first.

**4. Make state visible, always.**
Print the state dict after every run. Call `graph.get_graph().draw_mermaid()`. Students should never imagine the graph.

**5. Be precise about what is new vs what S10f already shipped.**
Notebook 11 already used `interrupt()` via `HumanInTheLoopMiddleware` and `checkpointer=` / `Store` on `create_agent`. S11 shows the *primitive*, applied to a decision no generic middleware packages ("we retried retrieval and generation and are still not confident — escalate").

**6. The optional capstone must extend prior work.**
`capstone_agentic_rag/` imports `HybridIndex`, `Reranker`, and prompts from `10_RAG/notebooks/production_rag_chatbot/rag_pipeline.py`. Do not re-teach retrieval.

**7. Assess with a trace, not just a final answer.**
Did it grade a weak retrieval as insufficient? Rewrite sensibly? Escalate instead of hallucinating? A correct answer that skipped grading is a fail.

---

## Coverage map — every Module 10 tool, and where it lives here

| Module 10 tool / technique | Notebook it was taught in | Used in S11 how |
|---|---|---|
| Recursive chunking | S10b (Notebook 02) | Reused via `chunk_documents()`, imported unmodified |
| Dense embeddings (bge-small) + Chroma | S10c (Notebooks 04/05) | Reused via `HybridIndex` |
| BM25 sparse retrieval | S10d (Notebook 06) | Reused via `HybridIndex` |
| RRF hybrid fusion | S10d (Notebook 07) | Reused via `HybridIndex.search()` |
| Cross-encoder reranking | S10d (Notebook 08) | Reused via `Reranker` |
| `min_rerank_score` guardrail | Notebook 13 | `grade_documents()` pre-filter |
| RAGAS Faithfulness | S10e (Notebook 09) | `check_groundedness()` live (LLM-judge fallback) |
| Condense-question memory | Notebook 13 | `condense()` on graph state |
| Short-term memory (checkpointer) | S10f (Notebook 11) | `builder.compile(checkpointer=...)` |
| Token-budget trimming | S10f §5b | `trim_history()` |
| Long-term memory (`Store`) | S10f §6 | `recall_preferences()` / `remember_answer_style()` |
| Resilience (retry/fallback) | S10f §10 | `resilient_invoke()` |
| Structured output | S10f §11 | `extract_structured_citations()` |
| Human-in-the-loop | S10f §9 | `human_escalation()` |
| Observability | S10f §12 | `LANGSMITH_*` env vars + Streamlit trace panel |
| Testing | S10f §13 | `capstone_agentic_rag/tests/test_graph.py` |
| DeepEval | S10e (Notebook 10) | Extension point (RAGAS already covers grounding) |
| FAISS · Pinecone | S10c (Notebook 05) | Extension point (`HybridIndex` uses Chroma) |
| SPLADE | S10d (Notebook 06) | Extension point (BM25 is the sparse half) |
| FlashRank / Cohere rerank | S10d (Notebook 08) | Extension point |
| Multimodal RAG | Notebook 15 | Out of scope for the text capstone |
| MCP agents | Notebook 16 | Reused: Day 3 starts `production_mcp_agents_rag_capstone/mcp_server.py` |

---

## Real-world use cases (beyond the capstone)

| Use case | Why a graph, not a chain |
|---|---|
| Customer support triage | Router → specialist subgraphs → supervisor merge |
| Code review agent | Loop: lint/tests → fix → re-run until green (S09 loop as a graph) |
| Approval-gated automation | `interrupt()` before email / trade / delete |
| Deep research | `Send` fans a topic into parallel sub-searches |
| Long-running assistant | `Store` recalls preferences across days |

---

## Sources

- [LangChain & LangGraph v1.0](https://www.langchain.com/blog/langchain-langgraph-1dot0)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Self-reflective RAG with LangGraph](https://www.langchain.com/blog/agentic-rag-with-langgraph)
