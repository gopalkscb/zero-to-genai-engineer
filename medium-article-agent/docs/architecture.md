# Architecture — Medium Article Agent

## Status: All phases complete (1–8)

## Overview

LangGraph editorial pipeline: multi-format ingest → plan → optional web research → draft → images → parallel review loop (five specialists + deterministic house-skill lint) → editor score → style terminal stage → human gate → export.

The compiled graph uses `interrupt_before=["human_gate"]` (not an in-node `interrupt()` call).

## Backend (`backend/app/`)

| Module | Purpose |
|--------|---------|
| `config.py` | pydantic-settings; style guide path relative to backend root |
| `graph/state.py` | Typed state + reducers |
| `graph/build_graph.py` | Full graph: `Send()` fan-out + HITL interrupt |
| `graph/nodes/` | Pipeline nodes (23 named nodes in the compiled graph) |
| `llm/` | Provider-agnostic client + OpenAI + Bedrock |
| `parsing/` | PDF, PPTX, HTML, ipynb, text/transcript |
| `api/` | Pipeline, export, SSE routes |
| `events/event_bus.py` | In-process pub/sub for SSE |
| `observability/langsmith.py` | Tracing toggle |
| `persistence/` | SQLite run records |

## Frontend (`frontend/src/`)

Cloudscape workspace: upload, monitoring, log feed, Medium preview, house-skill checklist, source inspector, approve/export.

## Verification

```bash
cd backend && pytest tests/ -v          # 89 passed, 1 skipped (Bedrock live) with no API key
uvicorn app.main:app --port 8000        # /health
cd frontend && npm test && npm run build
```

## Deployment

- `backend/Dockerfile` — Python 3.12 image with `app/`, `prompts/`, `skills/`
- `docker-compose.yml` — local demo: API `:8000` + Vite `:5173` (proxies to `backend:8000`)
- Install, env vars, and production notes: [`README.md`](../README.md)
