from app.graph.state import LogEntry, LogLevel
from app.graph.trace import build_run_trace, history_from_logs, word_count


def test_history_from_supervisor_logs():
    logs = [
        LogEntry(node="draft", level=LogLevel.INFO, message="Draft generated (1000 chars)"),
        LogEntry(node="supervisor", level=LogLevel.INFO, message="Iteration 0: 18 open finding(s)", iteration=0),
        LogEntry(node="rewrite", level=LogLevel.INFO, message="Rewrite iteration 1 complete", iteration=1),
        LogEntry(node="supervisor", level=LogLevel.INFO, message="Iteration 1: 16 open finding(s)", iteration=1),
        LogEntry(node="supervisor", level=LogLevel.INFO, message="Iteration 5: 17 open finding(s)", iteration=5),
    ]
    history = history_from_logs(logs, "# Title\n\nHello world")
    opens = [item.open_findings_count for item in history if item.phase == "review"]
    assert 18 in opens and 16 in opens and 17 in opens
    assert history[-1].markdown.startswith("# Title")


def test_word_count():
    assert word_count("Hello brave world") == 3


def test_build_run_trace_visits():
    state = {
        "logs": [
            LogEntry(node="ingest", message="Ingesting 2 file(s)"),
            LogEntry(node="plan", message="Plan created"),
            LogEntry(node="supervisor", message="Iteration 0: 4 open finding(s)"),
        ],
        "final_markdown": "# Demo\n\nBody",
        "open_findings": [],
        "iteration": 0,
    }
    trace = build_run_trace(state)
    assert trace["node_visits"]["ingest"] == 1
    assert trace["graph"]["nodes"]
    assert trace["graph"]["edges"][0]["from"] == "ingest"
    assert any(edge.get("kind") == "loop" for edge in trace["graph"]["edges"])
    assert trace["title"] == "Demo"


def test_series_rebuilt_when_only_terminal_snapshot_survives():
    """A run whose per-iteration snapshots were dropped still charts from its logs."""
    state = {
        "logs": [
            LogEntry(node="supervisor", message="Iteration 0: 8 open finding(s)", iteration=0),
            LogEntry(node="supervisor", message="Iteration 1: 5 open finding(s)", iteration=1),
            LogEntry(node="supervisor", message="Iteration 2: 2 open finding(s)", iteration=2),
        ],
        "iteration_history": [
            {"iteration": 2, "phase": "final", "summary": "Final rewrite complete"},
        ],
        "final_markdown": "# Demo\n\nBody",
    }
    trace = build_run_trace(state)
    opens = [point["open"] for point in trace["findings_series"]]
    assert opens == [8, 5, 2]


def test_node_visits_count_passes_not_log_lines():
    from app.graph.trace import node_visits
    from app.graph.state import NodeEvent

    events = [
        NodeEvent(node="ingest", message="a", iteration=0),
        NodeEvent(node="ingest", message="b", iteration=0),
        NodeEvent(node="supervisor", message="pass 0", iteration=0),
        NodeEvent(node="rewrite", message="fix 1", iteration=1),
        NodeEvent(node="supervisor", message="pass 1", iteration=1),
    ]
    visits = node_visits(events)
    assert visits["ingest"] == 1
    assert visits["rewrite"] == 1
    assert visits["supervisor"] == 2
