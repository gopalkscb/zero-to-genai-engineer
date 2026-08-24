# MCP helpdesk (RAG + SQL tools)

Capstone from **Notebook 16**. An MCP server that exposes helpdesk tools (knowledge-base search, tickets, SQL). Session 11 Day 3 starts this process and puts a LangGraph team on top of it.

```bash
cd 10_RAG/notebooks/production_mcp_agents_rag_capstone
pip install -r requirements.txt
python seed_data.py          # first run: create/seed the local helpdesk DB
python mcp_server.py
```

Needs `OPENAI_API_KEY` in `10_RAG/.env`. Imports `../production_rag_chatbot/rag_pipeline.py`.

Standalone checks (no MCP client required):

```bash
python test_tools_standalone.py
python test_mcp_protocol.py
```

← [Notebooks](../README.md) · [Session 10](../../README.md) · used by [S11 Day 3](../../../11_LangGraph/multi_agent_orchestrator/)
