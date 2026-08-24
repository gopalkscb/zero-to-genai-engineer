<div align="center">

# Medium Article Agent

LangGraph editorial pipeline. Upload notes, slides, or a PDF. It plans, drafts, runs six reviewers, pauses for you, and exports Medium-ready Markdown.

**It does not post to Medium.** You copy the export.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agents-00A3A1?style=for-the-badge)](https://www.langchain.com/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

</div>

**GitHub:** [nursnaaz/medium-article-agent](https://github.com/nursnaaz/medium-article-agent)  
Taught as Session 11 extra in [Zero to GenAI Engineer](https://github.com/nursnaaz/zero-to-genai-engineer).

---

## What it does

```
ingest → plan → web_research (optional) → draft → image_gen
  → image_review ⇄ image_redraw (cap 2)
  → 6 reviewers in parallel (technical, style, structure, grounding, reader, house-skill lint)
  → supervisor → rewrite → rewrite_voice → reviewers again
  → editor_score (1–10, bar 8) → rewrite if below bar
  → headline → style_pass → final_rewrite → grounding_recheck
  → human_gate (you type yes / change this) → export Markdown
```

Full graph: [`docs/langgraph-diagram.mmd`](docs/langgraph-diagram.mmd).

| You get | Detail |
|---|---|
| Five source formats | PDF, PPTX, HTML, Jupyter notebooks, plain text |
| A real review loop | Ships only if the editor score clears 8/10 |
| A pause button | `interrupt()` before export — nothing goes out unsupervised |
| Two ways to run | Local venv, or `docker compose up` |
| Two LLM backends | OpenAI (default) or AWS Bedrock |

---

## Quick start

### Local

```bash
git clone https://github.com/nursnaaz/medium-article-agent.git
cd medium-article-agent
cp .env.example .env          # paste OPENAI_API_KEY

cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

If you already cloned the course repo, the same app is at `medium-article-agent/` in [zero-to-genai-engineer](https://github.com/nursnaaz/zero-to-genai-engineer). Commands above are the same from that folder.

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

---

## Environment

| Variable | Default | What it is |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `bedrock` |
| `OPENAI_API_KEY` | | Required for OpenAI |
| `MODEL_PLAN` | `gpt-4o-mini` | Planning model |
| `MODEL_DRAFT` | `gpt-4o` | Draft model |
| `MEDIUM_STYLE_GUIDE_PATH` | `skills/medium.md` | Relative to `backend/` |
| `MAX_REVIEW_ITERATIONS` | `12` | Review loop ceiling |
| `EDITOR_SCORE_THRESHOLD` | `8.0` | Minimum score to ship |
| `TRACING_ENABLED` | `false` | LangSmith |

Optional DuckDuckGo research sits between plan and draft. Off by default; turn it on in the upload form. Uploaded files stay the source of truth. Search snippets are citations and current examples only.

Copy `.env.example` to `.env`. Never commit `.env`.

---

## Style guide

House style lives at `backend/skills/medium.md`. Ingest loads the full file. Plan and draft see all of it. Later writer, reviewer, and editor nodes get a compact checklist from sections 3, 5, 9, and 10. A deterministic lint catches banned phrases, dashes, word count, H2 spacing, and the AI disclosure. The Story tab shows the live checklist.

---

## API

| Method | Path | |
|---|---|---|
| GET | `/health` | Health + style guide status |
| GET | `/api/pipeline/config` | Config |
| POST | `/api/pipeline/start` | Upload files, start a run |
| GET | `/api/pipeline/{run_id}/status` | Status |
| POST | `/api/pipeline/{run_id}/approve` | Human gate: approve or request changes |
| GET | `/api/stream/{run_id}` | SSE log stream |
| GET | `/api/export/{run_id}` | Export artifacts |
| GET | `/api/export/{run_id}/clipboard` | Clipboard payload |

---

## Tests

```bash
cd backend
pytest tests/ -v
```

Covers parsing (five formats, tables, notebook outputs), house-skill lint, supervisor exit gate, em/en dash check, and a mocked graph smoke test.

```bash
# OpenAI (default)
LLM_PROVIDER=openai pytest tests/test_graph_smoke.py

# Bedrock (needs AWS credentials)
LLM_PROVIDER=bedrock pytest tests/test_graph_smoke.py
```

Nodes never hardcode model IDs. Swap providers with `LLM_PROVIDER`.

---

## Deploy notes (Bedrock / AgentCore)

1. Set `LLM_PROVIDER=bedrock` plus `AWS_REGION`, credentials, and `BEDROCK_MODEL_*` inference profile IDs.
2. Build and push the backend Docker image (it includes `skills/`).
3. Run on AgentCore or ECS with a volume for `backend/data/`, Secrets Manager for keys, and `bedrock:InvokeModel` on the task role.

LangSmith (`TRACING_ENABLED=true`) is useful in development. On AWS, CloudWatch is the usual production complement.

---

## Layout

```
medium-article-agent/
├── backend/
│   ├── app/           FastAPI, LangGraph nodes, LLM client, parsers
│   ├── prompts/       Jinja2 templates
│   ├── skills/        medium.md house style
│   └── tests/
├── frontend/          React UI
├── docs/              graph diagram
├── docker-compose.yml
└── .env.example
```

---

## License

[MIT](./LICENSE). Built by Mohamed Noordeen Alaudeen as part of [Zero to GenAI Engineer](https://github.com/nursnaaz/zero-to-genai-engineer).
