"""Progress, resume, and last_node behaviour the mocked smoke tests missed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.graph.nodes.image_gen import image_gen_node
from app.graph.runtime import reset
from app.graph.state import ArticlePlan, LogEntry, PyramidSection
from app.graph.trace import build_run_trace
from app.main import create_app


def teardown_function():
    reset()


def test_last_node_follows_current_node_not_last_log():
    """The UI used last log, so it sat on Draft while image_gen was running."""
    state = {
        "logs": [LogEntry(node="draft", message="Draft generated (4661 chars)")],
        "current_node": "image_gen",
        "status": "running",
        "final_markdown": "# Title\n\nBody",
    }
    trace = build_run_trace(state)
    assert trace["last_node"] == "image_gen"


def test_image_gen_logs_start_before_openai(tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_COUNT", "2")
    monkeypatch.setenv("IMAGE_COUNT_MAX", "2")
    calls: list[str] = []

    class FakeClient:
        def generate(self, prompt):
            calls.append(prompt)
            return b"\x89PNG\r\n\x1a\n"

        def save(self, img_bytes, path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(img_bytes)
            return str(path)

    with patch("app.graph.nodes.image_gen.ImageClient", return_value=FakeClient()):
        with patch("app.graph.nodes.image_gen.get_settings") as settings:
            settings.return_value.image_count = 2
            settings.return_value.image_count_max = 2
            settings.return_value.image_aspect_ratio = "16:9"
            settings.return_value.data_dir = tmp_path
            result = image_gen_node(
                {
                    "run_id": "progress-run",
                    "draft_markdown": "# Title\n\nIntro\n\n## One\n\nA\n\n## Two\n\nB\n",
                    "plan": ArticlePlan(
                        title="Title",
                        thesis="Thesis",
                        pyramid_outline=[PyramidSection(level=1, title="One", bullets=["A"])],
                        image_prompts=["cover", "section"],
                    ),
                }
            )

    messages = [item.message for item in result["logs"]]
    assert any("Starting image generation" in msg for msg in messages)
    assert any("Generating figure 1/" in msg for msg in messages)
    start_at = next(i for i, msg in enumerate(messages) if "Starting image generation" in msg)
    first_fig = next(i for i, msg in enumerate(messages) if "Generating figure 1/" in msg)
    done_at = next(i for i, msg in enumerate(messages) if msg.startswith("Generated image"))
    assert start_at < first_fig < done_at
    assert calls  # generate was actually invoked after the start log existed


def test_resume_endpoint_kicks_pipeline_from_checkpoint():
    captured: dict = {}

    async def fake_run(run_id, uploaded_files, topic_hint, enable_web_research=False, resume=False):
        captured["run_id"] = run_id
        captured["resume"] = resume

    record = MagicMock()
    record.status = "running"
    record.topic_hint = ""
    app = create_app()
    with (
        patch("app.api.routes_pipeline._run_pipeline", new=AsyncMock(side_effect=fake_run)),
        patch("app.api.routes_pipeline._repo.get_run", return_value=record),
        patch("app.api.routes_pipeline._checkpoint_next", new=AsyncMock(return_value=["image_gen"])),
        patch("app.api.routes_pipeline.runtime.is_active", return_value=False),
    ):
        client = TestClient(app)
        response = client.post("/api/pipeline/070e91a4-07a9-4122-98f5-d49cc4b52894/resume")
    assert response.status_code == 200
    body = response.json()
    assert body["resumed"] is True
    assert body["next_nodes"] == ["image_gen"]
    assert captured["resume"] is True
    assert captured["run_id"] == "070e91a4-07a9-4122-98f5-d49cc4b52894"
