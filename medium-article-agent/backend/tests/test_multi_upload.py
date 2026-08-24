"""Unit + integration coverage for attaching more than one source file."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.graph.nodes.ingest import ingest_node
from app.main import create_app
from app.parsing import parse_upload
from app.parsing.normalize import combine_text, normalize_documents


def test_ingest_keeps_every_uploaded_file():
    state = ingest_node(
        {
            "run_id": "multi-1",
            "uploaded_files": [
                {
                    "content": b"BPE starts from characters and merges frequent pairs.",
                    "filename": "bpe.txt",
                    "source_id": "src1",
                },
                {
                    "content": b"Token count is what you are billed for.",
                    "filename": "billing.md",
                    "source_id": "src2",
                },
            ],
        }
    )
    names = [doc.filename for doc in state["documents"]]
    assert names == ["bpe.txt", "billing.md"]
    assert "=== bpe.txt" in state["combined_text"]
    assert "=== billing.md" in state["combined_text"]
    assert "Ingesting 2 file(s)" in state["logs"][0].message
    parsed_logs = [item.message for item in state["logs"] if item.message.startswith("Parsed ")]
    assert any("bpe.txt" in message for message in parsed_logs)
    assert any("billing.md" in message for message in parsed_logs)


def test_combine_text_separates_sources():
    docs = normalize_documents(
        [
            parse_upload(b"First source body.", "first.txt", "src1"),
            parse_upload(b"Second source body.", "second.txt", "src2"),
        ]
    )
    combined = combine_text(docs)
    assert combined.index("First source body.") < combined.index("Second source body.")
    assert combined.count("=== first.txt") == 1
    assert combined.count("=== second.txt") == 1


def test_start_api_accepts_multiple_files():
    captured: dict = {}

    async def fake_run(run_id, uploaded_files, topic_hint, enable_web_research=False, resume=False):
        captured["run_id"] = run_id
        captured["files"] = uploaded_files
        captured["topic"] = topic_hint
        captured["web"] = enable_web_research

    app = create_app()
    with (
        patch("app.api.routes_pipeline._run_pipeline", new=AsyncMock(side_effect=fake_run)),
        patch("app.api.routes_pipeline._repo.create_run", return_value="test-run-multi"),
        patch("app.api.routes_pipeline._repo.update_run"),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/pipeline/start",
            data={"topic_hint": "two sources", "enable_web_research": "false"},
            files=[
                ("files", ("alpha.txt", b"alpha source about BPE", "text/plain")),
                ("files", ("beta.txt", b"beta source about tokens", "text/plain")),
            ],
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert captured["run_id"] == body["run_id"]
    assert [item["filename"] for item in captured["files"]] == ["alpha.txt", "beta.txt"]
    assert captured["files"][0]["content"] == b"alpha source about BPE"
    assert captured["files"][1]["content"] == b"beta source about tokens"
    assert captured["files"][0]["source_id"] == "src1"
    assert captured["files"][1]["source_id"] == "src2"


def test_start_api_rejects_zero_files():
    app = create_app()
    with (
        patch("app.api.routes_pipeline._run_pipeline", new=AsyncMock()),
        patch("app.api.routes_pipeline._repo.create_run", return_value="test-run-empty"),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/pipeline/start",
            data={"topic_hint": "none", "enable_web_research": "false"},
        )
    assert response.status_code == 422
