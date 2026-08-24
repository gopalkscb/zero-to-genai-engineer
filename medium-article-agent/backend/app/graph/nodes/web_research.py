"""Optional DuckDuckGo research after plan, before draft."""

from __future__ import annotations

from app.graph.state import AgentState, ArticlePlan, LogEntry, LogLevel, WebResearch, WebSnippet

MAX_QUERIES = 4
RESULTS_PER_QUERY = 3


def build_research_queries(plan: ArticlePlan | None, topic_hint: str = "") -> list[str]:
    """Derive a small query set from the plan. No extra LLM call."""
    queries: list[str] = []
    hint = (topic_hint or "").strip()
    if hint:
        queries.append(hint)
    if plan:
        if plan.title:
            queries.append(plan.title)
        if plan.thesis:
            queries.append(plan.thesis[:180])
        for section in plan.pyramid_outline[:2]:
            title = f"{plan.title} {section.title}".strip()
            if title:
                queries.append(title)

    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
        if len(unique) >= MAX_QUERIES:
            break
    return unique


def _search_duckduckgo(query: str) -> list[WebSnippet]:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS  # type: ignore

    snippets: list[WebSnippet] = []
    with DDGS() as client:
        rows = client.text(query, max_results=RESULTS_PER_QUERY) or []
    for row in rows:
        snippets.append(
            WebSnippet(
                query=query,
                title=str(row.get("title") or ""),
                url=str(row.get("href") or row.get("url") or ""),
                snippet=str(row.get("body") or row.get("snippet") or ""),
            )
        )
    return snippets


def web_research_node(state: AgentState) -> dict:
    enabled = bool(state.get("enable_web_research"))
    if not enabled:
        return {
            "web_research": WebResearch(enabled=False),
            "logs": [
                LogEntry(
                    node="web_research",
                    level=LogLevel.INFO,
                    message="Web research skipped (disabled)",
                )
            ],
        }

    queries = build_research_queries(state.get("plan"), state.get("topic_hint", ""))
    snippets: list[WebSnippet] = []
    errors = 0
    for query in queries:
        try:
            snippets.extend(_search_duckduckgo(query))
        except Exception:
            errors += 1

    research = WebResearch(enabled=True, queries=queries, snippets=snippets)
    message = f"Web research: {len(snippets)} snippet(s) from {len(queries)} quer{'y' if len(queries) == 1 else 'ies'}"
    if errors:
        message += f" ({errors} query failure(s))"

    return {
        "web_research": research,
        "logs": [
            LogEntry(
                node="web_research",
                level=LogLevel.WARNING if errors and not snippets else LogLevel.INFO,
                message=message,
            )
        ],
    }
