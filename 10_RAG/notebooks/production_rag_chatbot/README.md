# Production RAG chatbot

Streamlit app built in **Notebook 13**. Uses `rag_pipeline.py` (`HybridIndex` + `Reranker` + grounded generation).

Session 11's self-correcting RAG **imports this package unmodified** — do not rename or move this folder.

```bash
cd 10_RAG/notebooks/production_rag_chatbot
pip install -r requirements.txt
# needs OPENAI_API_KEY in 10_RAG/.env (or the repo root)
streamlit run app.py
```

Demo prompts: [`DEMO_QUESTIONS.md`](DEMO_QUESTIONS.md).

← [Notebooks](../README.md) · [Session 10](../../README.md)
