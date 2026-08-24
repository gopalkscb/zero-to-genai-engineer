# Architecture — Medium Article Agent

## Status: All Phases Complete (1–8)

## Overview

LangGraph editorial pipeline: multi-format ingest → plan → draft → images → parallel review loop (including deterministic house-skill lint) → style terminal stage → human gate → export.

## Backend (`backend/app/`)

| Module | Purpose |
|--------|---------|
| `config.py` | pydantic-settings; style guide path relative to backend root |
| `graph/state.py` | Section 5 hard contracts + reducers |
| `graph/build_graph.py` | Full graph with Send() fan-out + HITL interrupt |
| `graph/nodes/` | 15 pipeline nodes |
| `llm/` | Provider-agnostic client + OpenAI + Bedrock |
| `parsing/` | PDF, PPTX, HTML, ipynb, transcript parsers |
| `api/` | Pipeline, export, SSE routes |
| `events/event_bus.py` | In-process pub/sub for SSE |
| `observability/langsmith.py` | Tracing toggle |
| `persistence/` | SQLite run records |

## Frontend (`frontend/src/`)

Cloudscape workspace: upload, monitoring, log feed, Medium preview, house-skill checklist, source inspector, approve/export.

## Verification

```bash
cd backend && pytest tests/ -v          # 19 passed
uvicorn app.main:app --port 8000        # /health
cd frontend && npm run build            # production build
```

## Deployment

- `backend/Dockerfile` — includes `skills/`
- `docker-compose.yml` — backend + frontend dev
- See `README.md` for AgentCore path
