<div align="center">

# 🤖 Zero to GenAI Engineer

### From complete beginner → production AI engineer — one weekend at a time.

[![GitHub stars](https://img.shields.io/github/stars/nursnaaz/zero-to-genai-engineer?style=for-the-badge&logo=github)](https://github.com/nursnaaz/zero-to-genai-engineer)
[![GitHub forks](https://img.shields.io/github/forks/nursnaaz/zero-to-genai-engineer?style=for-the-badge&logo=github)](https://github.com/nursnaaz/zero-to-genai-engineer/fork)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0-1C3C3C?style=for-the-badge)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agents-00A3A1?style=for-the-badge)](https://www.langchain.com/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mohamed_Noordeen-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/nursnaaz)
[![AWS](https://img.shields.io/badge/AWS-GenAI_Innovation_Center-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://linkedin.com/in/nursnaaz)

**Real code · Real papers · Real datasets · Real apps · Built to get you hired**

[Start here](#-start-here) · [Prerequisites](#-prerequisites) · [Syllabus](#-full-syllabus-every-session) · [S10 RAG](#s10--rag--memory--chatbots-m07--m08--m06) · [S11 LangGraph](#s11--langgraph-stateful-agents-m10) · [Projects](#-projects-you-can-ship) · [Contributing](#-contributing)

</div>

---

| 13 sessions | 57 notebooks | 12 research papers | 19 HTML decks |
|:---:|:---:|:---:|:---:|
| Pre-work → S11 | Colab-ready, commented | GPT-1 → DPO + Attention | Open in any browser |
| **9 industry RAG briefs** | **10 in-repo apps** | **18 RAG notebooks** | **5 LangGraph notebooks** |
| Banking → insurance | Streamlit · FastAPI · React | Chunking → MCP helpdesk | Graphs · HITL · teams |

New sessions drop every **Saturday / Sunday**. Star the repo to get notified. Questions → **WhatsApp cohort group**.

---

## Table of contents

1. [Start here](#-start-here)
2. [Prerequisites](#-prerequisites)
3. [What's in this repo](#-whats-in-this-repo)
4. [The MISSING chain](#-the-missing-chain)
5. [Your instructor](#-your-instructor)
6. [How this repo is laid out](#-how-this-repo-is-laid-out)
7. [Sessions shipped so far](#-sessions-shipped-so-far)
8. [Full syllabus](#-full-syllabus-every-session)
9. [Projects](#-projects-you-can-ship)
10. [Classroom presentations](#-classroom-presentations-github-pages)
11. [Tech stack](#-tech-stack-when-each-tool-first-appears)
12. [Module map](#-where-the-23-module-syllabus-stands)
13. [Contributing](#-contributing)
14. [License](#-license)

---

## 🚀 Start here

| You are… | Do this |
|---|---|
| **New to Python / ML** | [`prereq/`](./prereq/) (~3 hours) → then **[S00](./00_How_Search_Engine_Works/)** |
| **Ready for the course** | Open the next session folder. **The README inside is the start page.** Run notebooks in order. |
| **On RAG + memory (S10)** | [`10_RAG/README.md`](./10_RAG/) — notebooks **01–12** required; **11 / 13 / 14** are the Memory & Chatbots track |
| **On LangGraph (S11)** | [`11_LangGraph/README.md`](./11_LangGraph/) — notebooks **01–03** required, **04–05** bonus |
| **Caught up through S11** | Ship a [portfolio piece](#-projects-you-can-ship). Memory & chatbots are **already in S10** — not a future module. |

Beginner notebooks (no install):

| Notebook | What you learn | Time |
|---|---|---|
| [01 — Python for GenAI](./prereq/notebooks/01_python_for_genai.ipynb) | Variables, loops, functions, dicts, f-strings | 60 min |
| [02 — Math Intuition](./prereq/notebooks/02_math_intuition.ipynb) | Vectors, dot product, softmax | 60 min |
| [03 — Neural Networks](./prereq/notebooks/03_neural_networks_intuition.ipynb) | How models learn — in plain English | 60 min |

Then keep the **[Cheat Sheet](./prereq/cheatsheet.md)** open during S00.

---

## ⚙️ Prerequisites

| Need | Detail |
|---|---|
| **Python** | **3.11+** (3.12 is fine). Session apps use `python3 -m streamlit` so the same env is used. |
| **Git** | Clone this repo. Do not copy-paste folders by hand. |
| **Notebooks** | [Google Colab](https://colab.research.google.com) (no install) **or** local Jupyter. |
| **API keys** | Early sessions (S00–S03, most of S04 NB1) need **none**. S04 NB2+ use Gemini. S10+ expect `OPENAI_API_KEY` in [`10_RAG/.env.example`](./10_RAG/.env.example). Optional: Anthropic, Cohere, Pinecone, Tavily, LangSmith — only when a notebook says so. |
| **Local models (S05 / S06 Ollama notebook)** | [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai) on your laptop. Not available in Colab. |
| **GPU** | Only S02 training wants Colab Pro / a real GPU. Everything else is CPU-friendly or API-backed. |
| **Node 18+** | Only for React apps (CineMatch, Distill, RAG Studio, Medium article agent). Streamlit-only paths do not need Node. |

```bash
git clone https://github.com/nursnaaz/zero-to-genai-engineer.git
cd zero-to-genai-engineer
```

Then open that weekend's folder README — **that file is the start page**. There is no single root `requirements.txt`; each session / app has its own (`10_RAG/notebooks/requirements.txt`, `11_LangGraph/notebooks/requirements.txt`, …).

Never commit a real `.env`. Copy the session `.env.example` instead.

---

## 📦 What's in this repo

This is not a slide dump. Every session has **code you run**, and most have **something you ship**.

| Kind of material | Count | Where it lives |
|---|---|---|
| Weekend sessions (S00–S11) + pre-work | **13** | Numbered folders + [`prereq/`](./prereq/) |
| Jupyter notebooks | **57** | Session `notebooks/` + 11 S03 paper summaries + 2 S10 student copies. Do not use the extra notebook in [`03_GPT_1_2_3/`](./03_GPT_1_2_3/) (legacy). |
| RAG teaching notebooks (01–16 + 2 student labs) | **18** | [`10_RAG/notebooks/`](./10_RAG/notebooks/) |
| LangGraph teaching notebooks | **5** | [`11_LangGraph/notebooks/`](./11_LangGraph/notebooks/) (plus optional `self_correcting_rag.ipynb` in the capstone folder) |
| Original research PDFs | **12** | S02 *Attention Is All You Need* + S03 GPT / BERT / alignment |
| Beginner paper-summary notebooks | **11** | [`03_GPT_Evolution_and_Alignment/paper_summaries/`](./03_GPT_Evolution_and_Alignment/paper_summaries/) |
| Classroom HTML decks | **19** | S03 papers (1) · S08 recap (2) · S10 (12) · S11 (4) |
| PDF slide decks | S00 (3) · S01 (1) · S02 (1) · S05 (`slides.pdf`) | Each session's `slides/` |
| Interactive browser tutorials | **5** | [nursnaaz.github.io](https://nursnaaz.github.io) |
| Student group RAG datasets | **9 companies** | [`10_RAG/student_group_datasets/`](./10_RAG/student_group_datasets/) |
| Shippable apps in this repo | **10** | See [Projects](#-projects-you-can-ship) |

**Folder number ≠ module number.** `10_RAG/` is session **S10** = modules **M07 + M08 + M06** (memory absorbed into the RAG chatbot). `11_LangGraph/` is session **S11** = module **M10**.

---

## 🔗 The MISSING chain

Every session answers one question: *"What was missing from the last one?"*  
That chain **is** the curriculum — not a pile of tutorials.

```text
S00  Search (TF-IDF)
  └─ MISSING: meaning  ─►  S01  Embeddings (BoW → FastText)
       └─ MISSING: context  ─►  S02  Transformers (self-attention)
            └─ MISSING: GPT story  ─►  S03  GPT-1→3 + alignment (11 papers)
                 └─ MISSING: tokens & sampling  ─►  S04  BPE / Temp / Top-K / Top-P
                      └─ MISSING: how to RUN a model  ─►  S05  Ollama · LM Studio · OpenRouter
                           └─ MISSING: better prompts  ─►  S06  DSPy · CoT · MIPROv2 · GEPA
                                └─ MISSING: one API for every model  ─►  S07  LangChain LCEL
                                     └─ S08 Recap (S00–S07 visual pass)
                                          └─ MISSING: AI that writes the code  ─►  S09  /goal · /loop
                                               └─ MISSING: YOUR documents  ─►  S10  RAG + memory + chatbots
                                                    └─ MISSING: loops, pause, teams  ─►  S11  LangGraph  ← you are here
```

---

## 👨‍🏫 Your instructor

<img align="right" src="https://github.com/nursnaaz.png" width="110"/>

**Mohamed Noordeen Alaudeen** — Data Scientist at **AWS Generative AI Innovation Center** · Dubai

- 🏆 Emerging Global Leader in GenAI — Internet 2.0 Conference Award (2024)
- 👥 29,000+ LinkedIn followers · 1,000+ professionals mentored
- 📚 Packt author (*Data Science Interview Questions*) · IIM Lucknow · 10+ years in AI/ML

> *"Learn GenAI the way professionals actually use it — not just theory, but systems that get you hired."*

---

## 📁 How this repo is laid out

One numbered folder per session. **Open that folder's README first.**

| Folder | Session | Open this |
|---|---|---|
| [`prereq/`](./prereq/) | Pre-work | 3 notebooks + cheat sheet |
| [`00_How_Search_Engine_Works/`](./00_How_Search_Engine_Works/) | S00 | 2 notebooks + 3 slide PDFs |
| [`01_Text_to_Numbers/`](./01_Text_to_Numbers/) | S01 | 2 notebooks + [CineMatch](./01_Text_to_Numbers/movie_recommender/) |
| [`02_Transformer_Architecture/`](./02_Transformer_Architecture/) | S02 | Notebook + Vaswani paper + 3 browser tutorials + animation |
| [`03_GPT_Evolution_and_Alignment/`](./03_GPT_Evolution_and_Alignment/) | S03 | GPT from scratch + 11 papers + 11 summaries + [▶ slides](https://nursnaaz.github.io/zero-to-genai-engineer/03_GPT_Evolution_and_Alignment/GPT_Papers_Presentation.html) |
| [`04_BPE_Temperature_Top_K_Top_P/`](./04_BPE_Temperature_Top_K_Top_P/) | S04 | 2 notebooks + 2 Excel workbooks |
| [`05_Local_LLMs_and_API_Providers/`](./05_Local_LLMs_and_API_Providers/) | S05 | 6 notebooks + 2 demo apps + [Distill](./05_Local_LLMs_and_API_Providers/distill/) |
| [`06_Prompt_Engineering_DSPY_GEPA_COT/`](./06_Prompt_Engineering_DSPY_GEPA_COT/) | S06 | DSPy → few-shot → MIPROv2 → GEPA (cloud + Ollama) |
| [`07_LangChain_Notebooks/`](./07_LangChain_Notebooks/) | S07 | One notebook: 4 providers · templates · history · streaming · LCEL |
| [`08_Recap/`](./08_Recap/) | S08 | [▶ Presentation](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_PRESENTATION.html) · [▶ Full text](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_SLIDES.html) |
| [`09_AgenticCoding_LoopEngineering/`](./09_AgenticCoding_LoopEngineering/) | S09 | [`AGENTIC_CODING_GUIDE.md`](./09_AgenticCoding_LoopEngineering/AGENTIC_CODING_GUIDE.md) · 20+ loop exercises |
| [`10_RAG/`](./10_RAG/) | S10 | **[Start →](./10_RAG/README.md)** 16 notebooks · 12 decks · 3 Streamlit/MCP apps · RAG Studio · 9 group briefs |
| [`11_LangGraph/`](./11_LangGraph/) | S11 | **[Start →](./11_LangGraph/README.md)** 5 notebooks · 4 decks · helpdesk orchestrator · agentic RAG |
| [`medium-article-agent/`](./medium-article-agent/) | S11 extra | FastAPI + React editorial graph |

`03_GPT_1_2_3/` is **legacy** — use [`03_GPT_Evolution_and_Alignment/`](./03_GPT_Evolution_and_Alignment/) instead.

---

## 🗺️ Sessions shipped so far

| Session | Topic | What you build | Hours (classroom) |
|---|---|---|---|
| [Pre-work](./prereq/) | Python · vectors · how NNs learn | 3 Colab notebooks + cheat sheet | ~3 |
| [S00](./00_How_Search_Engine_Works/) | How Search Engines Work | TF-IDF engine from scratch (no ML) | ~1.5 |
| [S01](./01_Text_to_Numbers/) | Text to Numbers | 5 embedding methods · [CineMatch](./01_Text_to_Numbers/movie_recommender/) | ~2 + project |
| [S02](./02_Transformer_Architecture/) | Transformer Architecture | Encoder–Decoder in PyTorch · EN→IT | ~2 + GPU train |
| [S03](./03_GPT_Evolution_and_Alignment/) | GPT Evolution & Alignment | GPT from scratch · 11 papers · [▶ slides](https://nursnaaz.github.io/zero-to-genai-engineer/03_GPT_Evolution_and_Alignment/GPT_Papers_Presentation.html) | ~8 |
| [S04](./04_BPE_Temperature_Top_K_Top_P/) | BPE & Sampling | Tokenize from scratch · temperature / top-k / top-p | ~2 |
| [S05](./05_Local_LLMs_and_API_Providers/) | Local LLMs & APIs | Ollama · LM Studio · OpenRouter · Databricks · Distill | ~3 |
| [S06](./06_Prompt_Engineering_DSPY_GEPA_COT/) | Prompt Optimisation | DSPy signatures · CoT · MIPROv2 · GEPA | ~4 |
| [S07](./07_LangChain_Notebooks/) | LangChain | One API for OpenAI · Claude · Gemini · Ollama | ~1 |
| [S08](./08_Recap/) | Recap | [▶ Presentation](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_PRESENTATION.html) | ~1 |
| [S09](./09_AgenticCoding_LoopEngineering/) | Agentic Coding | `/goal` vs `/loop` · [guide](./09_AgenticCoding_LoopEngineering/AGENTIC_CODING_GUIDE.md) | ~3 |
| [S10](./10_RAG/) | **RAG + Memory & Chatbots** | Chunking → hybrid → RAGAS → production chatbot with memory | ~14 + capstone |
| [S11](./11_LangGraph/) | **LangGraph** | `StateGraph` · HITL · multi-agent helpdesk · ReAct→ToT · SQL agent | ~8 + apps |

---

## 📚 Full syllabus (every session)

Each block lists **what was missing**, **what you open**, and **what you walk out able to do**. Open the session README for setup.

---

### Pre-work — Python, math, neural nets

> **Why it exists:** S00 assumes you can read Python and picture a vector. This closes that gap in ~3 hours. Nothing extra.

| # | Notebook | Topics | Time |
|---|---|---|---|
| 01 | [Python for GenAI](./prereq/notebooks/01_python_for_genai.ipynb) | Variables, lists, loops, dicts, f-strings, functions | 60 min |
| 02 | [Math intuition](./prereq/notebooks/02_math_intuition.ipynb) | Vectors, dot product, probability, softmax | 60 min |
| 03 | [Neural nets](./prereq/notebooks/03_neural_networks_intuition.ipynb) | How a model learns — in plain English | 60 min |

Also: [`prereq/cheatsheet.md`](./prereq/cheatsheet.md) — keep it open during S00.

---

### S00 — How Search Engines Work

> **MISSING after this:** TF-IDF misses `"car crash"` when you search `"automobile accident"`. That is why S01 exists.

| # | Open | You build | Time |
|---|---|---|---|
| 01 | [search_engine.ipynb](./00_How_Search_Engine_Works/notebooks/01_search_engine.ipynb) | Tokenise · stop words · stem · inverted index · TF-IDF rank | 30 min |
| 02 | [tfidf_explained.ipynb](./00_How_Search_Engine_Works/notebooks/02_tfidf_explained.ipynb) | Why raw counts fail · TF × IDF scored by hand | 45 min |

**Slides:** [GenAI intro](./00_How_Search_Engine_Works/slides/00_genai_intro.pdf) · [How search works](./00_How_Search_Engine_Works/slides/00_how_search_engine_works.pdf) · [Claude Code leak](./00_How_Search_Engine_Works/slides/00_claude_code_leak_summary.pdf)

**Browser:** [How Search Engines Work](https://nursnaaz.github.io/) (open that tutorial from the homepage · 45 min)

No API key. Pure Python.

---

### S01 — Text to Numbers

> **MISSING after this:** `"bank"` (river) and `"bank"` (finance) share one vector. S02 adds context.

| # | Open | You build | Time |
|---|---|---|---|
| 01 | [text_to_numbers.ipynb](./01_Text_to_Numbers/notebooks/01_text_to_numbers.ipynb) | BoW → TF-IDF → Word2Vec → GloVe → FastText | 60 min |
| 02 | [cosine_similarity.ipynb](./01_Text_to_Numbers/notebooks/02_cosine_similarity.ipynb) | Why cosine beats Euclidean for meaning | 30 min |

**App:** [CineMatch](./01_Text_to_Numbers/movie_recommender/) — FastAPI + React, 5 embedders on 1,000 IMDB movies.

**Assignments:** Medium article on the 5 methods · Medium article cosine vs Euclidean · product recommender (Amazon descriptions).

**Slides:** [`slides/M00-S01.pdf`](./01_Text_to_Numbers/slides/M00-S01.pdf)  
**Browser:** [Cosine Similarity & Movie Recommender](https://nursnaaz.github.io/) (open that tutorial from the homepage)

---

### S02 — Transformer Architecture

> **MISSING after this:** Training from scratch is expensive. S03 is how that architecture became GPT and then ChatGPT.

| Open | You build |
|---|---|
| [transformer_from_scratch.ipynb](./02_Transformer_Architecture/notebooks/01_transformer_from_scratch.ipynb) | `InputEmbeddings` · sinusoidal PE · LayerNorm · residual · FFN · 8-head attention · 6-layer encoder + decoder · EN→IT on `opus_books` |

**Paper:** [`Attention_Is_All_You_Need.pdf`](./02_Transformer_Architecture/papers/Attention_Is_All_You_Need.pdf)

**Browser tutorials (do these before the notebook):**

| Tutorial | Time |
|---|---|
| [Self-Attention](https://nursnaaz.github.io/) | 30 min |
| [Positional Encoding](https://nursnaaz.github.io/) | 35 min |
| [Multi-Head Attention](https://nursnaaz.github.io/) | 60 min |

**Assets:** `SelfAttentionFull.mp4` · attention GIF · architecture spreadsheet.

GPU note: building blocks run on CPU; the training loop wants **Colab Pro / H100**.

---

### S03 — GPT Evolution & Alignment

> **M00 (foundations) ends here.** S00–S03 take you from raw text to how modern assistants are trained and aligned.

**Path:** text prediction (GPT-1) → scale (GPT-2/3) → alignment (RLHF → CAI → DPO).

| Track | What you open |
|---|---|
| Overview slides | [▶ 14-slide paper deck](https://nursnaaz.github.io/zero-to-genai-engineer/03_GPT_Evolution_and_Alignment/GPT_Papers_Presentation.html) |
| NB2 — map | [TensorFlow minimal GPT](./03_GPT_Evolution_and_Alignment/notebooks/NB2_GPT_TensorFlow_Minimal_Synthetic.ipynb) (~30 min) |
| NB1 — deep dive | [PyTorch Holmes GPT](./03_GPT_Evolution_and_Alignment/notebooks/NB1_GPT_PyTorch_Detailed_Holmes.ipynb) (~2–3 hr) — char / word / BPE, AdamW, attention heatmaps |
| App | [`holmes_gpt_ui.py`](./03_GPT_Evolution_and_Alignment/holmes_gpt_ui.py) — Streamlit generator |

**11 papers (PDF + beginner summary notebook each):**

| # | Paper | Year | The question it answers |
|---|---|---|---|
| 1 | GPT-1 | 2018 | Does pre-train + fine-tune beat training from scratch? |
| 2 | GPT-2 | 2019 | What if we scale and drop task-specific fine-tuning? |
| 3 | GPT-3 | 2020 | What happens at 175B — few-shot in the prompt? |
| 4 | BERT | 2018 | What if we read both directions? |
| 5 | BART | 2019 | What if we combine BERT + GPT? |
| 6 | InstructGPT / RLHF | 2022 | How does GPT-3 become ChatGPT? |
| 7 | HH-RLHF | 2022 | Helpful *and* harmless — the Claude research |
| 8 | Constitutional AI | 2022 | Can a written constitution replace human safety labels? |
| 9 | RLAIF | 2023 | Does AI feedback match human feedback at scale? |
| 10 | DPO | 2023 | Can we align without a reward model / PPO? |
| 11 | SELF-REFINE | 2023 | Can a model improve its own outputs? |

Summaries: [`paper_summaries/`](./03_GPT_Evolution_and_Alignment/paper_summaries/). PDFs: [`papers/`](./03_GPT_Evolution_and_Alignment/papers/).

---

### S04 — BPE, Temperature, Top-K, Top-P

> **MISSING from S03:** How does the model turn words into IDs? How does it pick the *next* token?

| # | Open | You implement | Time |
|---|---|---|---|
| Excel | [`bpe_step_by_step.xlsx`](./04_BPE_Temperature_Top_K_Top_P/bpe_step_by_step.xlsx) | Watch merge rounds grow a vocab | 15 min |
| Excel | [`llm_temperature_topp_topk.xlsx`](./04_BPE_Temperature_Top_K_Top_P/llm_temperature_topp_topk.xlsx) | Sliders on a fixed distribution | 15 min |
| NB1 | [BPE Tokenization](./04_BPE_Temperature_Top_K_Top_P/notebooks/NB1_BPE_Tokenization.ipynb) | `build_bpe_vocab()` · `tokenize_with_bpe()` · tiktoken GPT-2 vs GPT-4 | 45 min |
| NB2 | [Temperature / Top-K / Top-P](./04_BPE_Temperature_Top_K_Top_P/notebooks/NB2_Temperature_TopK_TopP.ipynb) | `apply_temperature()` · filters · Gemini experiments · `sample_token()` in the correct order | 45 min |

**Order that matters:** temperature → top-K → top-P → sample. Getting this wrong is a common production bug.

---

### S05 — Local LLMs & API Providers

> **MISSING from S04:** One provider's API is a lock-in. This session: run local for free, or switch cloud with one variable.

| # | Notebook | Where it runs | Time |
|---|---|---|---|
| NB1 | [Multi-provider `chat()`](./05_Local_LLMs_and_API_Providers/notebooks/NB1_multi_provider_api_calls.ipynb) | Colab or local — OpenAI · Gemini · Anthropic · Ollama · OpenRouter · Databricks | 30 min |
| NB2 | [Map-reduce summariser](./05_Local_LLMs_and_API_Providers/notebooks/NB2_map_reduce_summarizer.ipynb) | Split a 50-page doc → map → reduce | 45 min |
| NB3 | [Ollama](./05_Local_LLMs_and_API_Providers/notebooks/NB3_Ollama_Local_Setup.ipynb) | **Laptop only** — Phi-3 / Llama 3.2 | 45 min |
| NB4 | [OpenRouter](./05_Local_LLMs_and_API_Providers/notebooks/NB4_OpenRouter_Multi_Provider.ipynb) | One key, 100+ models, cost compare | 20 min |
| NB5 | [LM Studio](./05_Local_LLMs_and_API_Providers/notebooks/NB5_LMStudio_Local_Setup.ipynb) | **Laptop only** — OpenAI-compatible `:1234` | 30 min |
| NB6 | [Databricks serving](./05_Local_LLMs_and_API_Providers/notebooks/NB6_Databricks_Endpoint.ipynb) | Enterprise REST pattern | 15 min |

**Demos:** [`apps/multi_provider_race.py`](./05_Local_LLMs_and_API_Providers/apps/multi_provider_race.py) · [`apps/map_reduce_demo.py`](./05_Local_LLMs_and_API_Providers/apps/map_reduce_demo.py)

**Portfolio:** [Distill](./05_Local_LLMs_and_API_Providers/distill/) — FastAPI + React + Whisper classroom tool ([contribute](https://github.com/nursnaaz/distill/blob/main/CONTRIBUTING.md)).

---

### S06 — Prompt Optimisation (DSPy · MIPROv2 · GEPA)

> **MISSING from S05:** We could call models. Prompts were still handwritten guesses. Treat them as **typed, versioned, scored code**.

| Day | Optimiser | What it changes | Artifact |
|---|---|---|---|
| **S06a** | `dspy.Signature` + `ChainOfThought` | Schema → prompt; visible `Reasoning:` | `cot_zero_shot.json` |
| **S06b** | LabeledFewShot | Random `k` demos | `cot_few_shot.json` |
| S06b | BootstrapFewShot | Keep only traces that pass the metric | `cot_boostraped_few_shot.json` |
| S06b | BootstrapFewShotWithRandomSearch | Best of N bootstrap runs | `cot_bootstraped_rs_few_shot.json` |
| **S06c** | **MIPROv2** | Searches the *instruction wording* + demos | `MiproV2Prompt.json` |
| **S06d** | **GEPA** | Rewrites the instruction from its own errors | generated in-notebook |

Benchmark used throughout: **ATIS** airline-intent (26 classes).

| File | Use when |
|---|---|
| [`dspy_training.ipynb`](./06_Prompt_Engineering_DSPY_GEPA_COT/dspy_training.ipynb) | Cloud — all four optimisers |
| [`dspy_training_ollama.ipynb`](./06_Prompt_Engineering_DSPY_GEPA_COT/dspy_training_ollama.ipynb) | Local, no API key |

---

### S07 — LangChain Fundamentals

> **MISSING from S06:** Each notebook talked to one provider with custom glue. LangChain is one interface.

| Notebook | Topics | Time |
|---|---|---|
| [langchain_claude_openai_gemini_ollama_stream.ipynb](./07_LangChain_Notebooks/langchain_claude_openai_gemini_ollama_stream.ipynb) | Unified chat · `ChatPromptTemplate` · `MessagesPlaceholder` · `InMemoryChatMessageHistory` · `.stream()` · LCEL `\|` pipes | 60 min |

Providers in the same notebook: `gpt-4o-mini` · Claude Haiku · Gemini Flash-Lite · Ollama `llama3.2` / `qwen2.5`.

---

### S08 — Recap (S00–S07)

Visual pass of the MISSING chain before agentic coding.

- [▶ Interactive presentation](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_PRESENTATION.html)
- [▶ Full-text slides](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_SLIDES.html)

---

### S09 — Agentic Coding & Loop Engineering

> **MISSING from S07:** You still typed every line. Spec the goal, verify with tests, loop until green.

| Day | Topic | You learn |
|---|---|---|
| **S09a** | Agentic coding | Prompting → ReAct → AutoGPT → RALPH → loop · what makes a good `/goal` · Kiro spec files |
| **S09b** | Loop engineering | `/goal` vs `/loop` · Trigger → Action → Verify → Decide → Stop · Claude Code hooks |

| File | What it is |
|---|---|
| [`AGENTIC_CODING_GUIDE.md`](./09_AgenticCoding_LoopEngineering/AGENTIC_CODING_GUIDE.md) | History, patterns, tooling |
| [`LOOP_ENGINEERING_PLAYBOOK.md`](./09_AgenticCoding_LoopEngineering/loop_demo/LOOP_ENGINEERING_PLAYBOOK.md) | **20+ exercises** |
| [`LoopEngineering.md`](./09_AgenticCoding_LoopEngineering/loop_demo/LoopEngineering.md) | Theory |

**Demo (external):** [Bullish Stock Scanner V3](https://github.com/nursnaaz/TechnicalStockPrediction/tree/feature/v3-high-precision) — FastAPI + React + **308 tests**, built through spec-driven loops.

---

### S10 — RAG + Memory & Chatbots (M07 + M08 + M06)

> **MISSING from S09:** Agents can write software. They still only know training data. RAG grounds answers in *your* PDFs, policies, and tickets.  
> **Memory & Chatbots (M06) is not a future folder.** Short-term memory, summarisation, long-term `Store`, condense-question, streaming, guardrails, and HITL shipped inside **S10f + notebooks 13–14**.

**Start page:** [`10_RAG/README.md`](./10_RAG/) · notebook index: [`10_RAG/notebooks/README.md`](./10_RAG/notebooks/)

```text
S10a  Why RAG
S10b  Chunking (LangChain) + same ideas in LlamaIndex
S10c  Embeddings → FAISS / Chroma / Pinecone
S10d  BM25 → hybrid (RRF) → reranking
S10e  RAGAS + DeepEval
S10f  Production chatbots = Memory & Chatbots track
S10g  Retrieval showdown on one Pinecone index
        │
        ├── 13–14  Production chatbot (+ durable memory)   capstone
        ├── 15      Multimodal RAG                          extra
        ├── 16      MCP helpdesk                            extra · required for S11c
        ├── RAG Studio                                      FastAPI + React portfolio
        └── 9 student group datasets                        real-company briefs
```

#### Core notebooks (required)

| Day | Notebook | Topic | Slides |
|---|---|---|---|
| **S10a** | [01 — Why RAG](./10_RAG/notebooks/01_why_rag_the_case_for_retrieval.ipynb) | Hallucination vs grounded retrieval | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_01_why_rag.html) |
| **S10b** | [02 — Chunking (LangChain)](./10_RAG/notebooks/02_ingestion_and_chunking_langchain.ipynb) | 6 chunking strategies | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_02_ingestion_chunking.html) |
| S10b | [03 — Chunking (LlamaIndex)](./10_RAG/notebooks/03_ingestion_and_chunking_llamaindex.ipynb) | Same ideas, second framework | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_03_ingestion_chunking_llamaindex.html) |
| **S10c** | [04 — Embeddings](./10_RAG/notebooks/04_embeddings.ipynb) | Geometry of meaning | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_04_embeddings.html) |
| S10c | [05 — Vector databases](./10_RAG/notebooks/05_vector_databases.ipynb) | FAISS → Chroma → Pinecone | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_05_vector_databases.html) |
| | Recap of 01–05 | | [▶ Revision](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/revision_notebooks_01_to_05.html) |
| **S10d** | [06 — Sparse retrieval](./10_RAG/notebooks/06_sparse_retrieval.ipynb) | BM25 vs dense vs SPLADE | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_06_why_bm25.html) |
| S10d | [07 — Hybrid search](./10_RAG/notebooks/07_hybrid_search.ipynb) | RRF / weighted fusion | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_07_why_hybrid.html) |
| S10d | [08 — Reranking](./10_RAG/notebooks/08_reranking.ipynb) | Cross-encoder / FlashRank / Cohere | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_08_why_reranking.html) |
| | Pipeline recap | | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_09_full_pipeline_recap.html) |
| **S10e** | [09 — RAGAS](./10_RAG/notebooks/09_ragas_evaluation.ipynb) | Faithfulness, relevancy, context precision / recall | |
| S10e | [10 — DeepEval](./10_RAG/notebooks/10_deepeval_evaluation.ipynb) | CI-native evals, hallucination, G-Eval | |
| **S10f** | [11 — Production chatbots](./10_RAG/notebooks/11_production_ready_chatbots.ipynb) | **Memory · streaming · guardrails · HITL** | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_11_production_chatbots.html) |
| **S10g** | [12 — Retrieval showdown](./10_RAG/notebooks/12_retrieval_showdown_pinecone.ipynb) | Dense vs BM25 vs hybrid on **one** Pinecone index | |

#### Memory & Chatbots — what S10f / 13 / 14 actually teach (M06)

This is the dedicated chatbot curriculum. It lives next to retrieval because production chat *is* RAG + memory.

| Topic | Where | What you can do after |
|---|---|---|
| Stateless vs `thread_id` | NB11 §2–3 | Same id remembers; new id is a new user |
| Short-term memory (checkpointer) | NB11 | `InMemorySaver` / SQLite — crash-safe turns |
| Token-budget trim (sliding window) | NB11 §5b | Drop oldest turns before the context explodes |
| Summarisation memory | NB11 | Auto-summarise when history crosses a token trigger |
| Long-term `Store` | NB11 §6 | Preferences that survive across threads |
| Condense-question | NB13 | Rewrite follow-ups ("what about *that* policy?") into a standalone query |
| Streaming tokens | NB11 | Token-by-token UI, not a spinner |
| Guardrails | NB11 | Refuse / block before a bad generation |
| Human-in-the-loop | NB11 §9 | Pause a risky tool until a human says yes |
| Observability | NB11 §12 | LangSmith traces |
| Production Streamlit bot | [NB13](./10_RAG/notebooks/13_capstone_production_rag_chatbot.ipynb) → [`production_rag_chatbot/`](./10_RAG/notebooks/production_rag_chatbot/) | Hybrid retrieve → rerank → generate + citations |
| Same bot + durable memory | [NB14](./10_RAG/notebooks/14_capstone_production_rag_chatbot_memory.ipynb) → [`production_rag_chatbot_memory/`](./10_RAG/notebooks/production_rag_chatbot_memory/) | Memory that lasts after you close the tab |
| Student labs | [13 STUDENT](./10_RAG/notebooks/13_capstone_production_rag_chatbot_STUDENT.ipynb) · [14 STUDENT](./10_RAG/notebooks/14_capstone_production_rag_chatbot_memory_STUDENT.ipynb) | Same pipeline, TODOs for you |

S11 **reuses** this memory stack (`condense()`, `trim_history()`, checkpointer, `Store`) — it does not re-teach it.

#### Capstones & extras

| Item | What it is |
|---|---|
| [15 — Multimodal RAG](./10_RAG/notebooks/15_multimodal_rag_images.ipynb) ([▶ slides](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_15_multimodal_rag.html)) | Images + text in one index |
| [16 — MCP helpdesk](./10_RAG/notebooks/16_capstone_mcp_agents_rag.ipynb) | RAG + SQL tools over MCP — **required before S11 Day 3** |
| **[RAG Studio](./10_RAG/capstone_rag_studio/)** | FastAPI + React — swap retrieval strategies side by side, RAGAS + DeepEval |
| **[9 group datasets](./10_RAG/student_group_datasets/)** | Real-company briefs (below) |

#### 9 student group datasets (cohort project)

Every group ships a cited, refusal-aware support bot and **8 ablation tables** (parse → chunk → embed → store → retrieve → fuse → rerank → generate). Spec: [`REQUIREMENTS_OVERVIEW.md`](./10_RAG/student_group_datasets/REQUIREMENTS_OVERVIEW.md) · metrics: [`EVALUATION_METHODOLOGY.md`](./10_RAG/student_group_datasets/EVALUATION_METHODOLOGY.md).

| # | Folder | Bot | Core skill | Data |
|---|---|---|---|---|
| 1 | [`01_banking`](./10_RAG/student_group_datasets/01_banking/) | Wells Fargo support | Grounded fee/policy Q&A | 3 PDF (60p) + XML |
| 2 | [`02_ecommerce`](./10_RAG/student_group_datasets/02_ecommerce/) | Amazon seller support | Seller-vs-buyer scope | 3 PDF (56p) + XML |
| 3 | [`03_telecom`](./10_RAG/student_group_datasets/03_telecom/) | Verizon support | Wireless / Fios / international routing | 3 PDF (40p) + XML |
| 4 | [`04_legal`](./10_RAG/student_group_datasets/04_legal/) | Law-firm contract search | Cross-doc retrieval + client attribution | 5 HTML (~105K words) |
| 5 | [`05_healthcare`](./10_RAG/student_group_datasets/05_healthcare/) | NIH-style health info | **Must refuse diagnosis** | 11k+ XML (download script) |
| 6 | [`06_finance_complaints`](./10_RAG/student_group_datasets/06_finance_complaints/) | Credit-rights helpline | ECOA vs Fair Housing routing | 4 PDF + CSV |
| 7 | [`07_airline_travel`](./10_RAG/student_group_datasets/07_airline_travel/) | Delta passenger support | Passenger-vs-cargo docs | 2 PDF (45p) + XML |
| 8 | [`08_tax_government`](./10_RAG/student_group_datasets/08_tax_government/) | IRS taxpayer help | Structured vs narrative retrieval | 3 PDF (244p) + CSV/XLS |
| 9 | [`09_insurance`](./10_RAG/student_group_datasets/09_insurance/) | State Farm support | State + product-line routing | 5 PDF (343p) + XLSX |

---

### S11 — LangGraph (stateful agents, M10)

> **MISSING from S10:** `ProductionRAGChatbot.chat()` is a **straight line**. It cannot retry retrieval, rewrite a vague question, or pause for a human. LangGraph is that control flow.

**Start page:** [`11_LangGraph/README.md`](./11_LangGraph/) · instructors: [`TEACHING.md`](./11_LangGraph/TEACHING.md) · notebooks: [`notebooks/README.md`](./11_LangGraph/notebooks/)

```text
S11a  Fundamentals & agents     required
S11b  Human-in-the-loop         required
S11c  Multi-agent orchestrator  required
  ├── S11d  Reasoning patterns  bonus (interview map)
  ├── S11e  SQL agent           bonus (Chinook)
  ├── capstone_agentic_rag/     optional self-correcting RAG
  └── medium-article-agent/     optional FastAPI + React
```

| Day | Open | You will be able to | Time | Slides |
|---|---|---|---|---|
| **S11a** | [01 — Fundamentals](./11_LangGraph/notebooks/01_langgraph_fundamentals_and_agents.ipynb) | Draw a graph · wire nodes/edges · build ReAct by hand · then `create_agent` · checkpointer · stream | ~2 hr | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_01_langgraph_fundamentals.html) |
| **S11b** | [02 — HITL](./11_LangGraph/notebooks/02_human_in_the_loop.ipynb) | `interrupt()` a risky tool · type yes/no · resume the **same** `thread_id` | ~1 hr | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_02_human_in_the_loop.html) |
| **S11c** | [03 — Orchestrator](./11_LangGraph/notebooks/03_multi_agent_orchestrator.ipynb) + [app](./11_LangGraph/multi_agent_orchestrator/) | Supervisor · RAG-as-tool · SQL over MCP · ticket writes pause | ~2 hr | taught live from the app |
| **S11d** | [04 — Patterns](./11_LangGraph/notebooks/04_agent_reasoning_patterns_masterclass.ipynb) | Name **ReAct · Reflection · Reflexion · REWOO · Tree-of-Thoughts · Self-Discover** and when to use each | ~2 hr | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_04_agent_reasoning_patterns.html) |
| **S11e** | [05 — SQL agent](./11_LangGraph/notebooks/05_sql_agent_langgraph.ipynb) | Force list-tables → schema → check → run on Chinook | ~1.5 hr | [▶](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_05_sql_agent.html) |

**API you actually type:** `StateGraph` · `MessagesState` · `ToolNode` · `tools_condition` · `Command` · `interrupt()` · `MemorySaver` · `InMemoryStore` · `create_agent` · `create_supervisor`.

**Day 3 graph (the one you run):**

```text
top_supervisor
  ├── knowledge_team → rag_agent (search_knowledge_base) + search_agent (web)
  └── ops_team       → sql_agent (reads) + ticket_agent (writes → interrupt())
```

```bash
cd 11_LangGraph/multi_agent_orchestrator
python3 -m streamlit run app.py
```

Try: *“What is our refund policy?”* · *“How many open tickets does Jane Doe have?”* · *“Add a note that we offered a refund”* (then type **yes** or **no**).

---

## 🏗️ Projects you can ship

| Project | Session | Stack | What a recruiter sees |
|---|---|---|---|
| **[Helpdesk Orchestrator](./11_LangGraph/multi_agent_orchestrator/)** | S11c | LangGraph · Streamlit · MCP | Hierarchical teams, RAG + SQL, write-tools that pause |
| **[Self-Correcting Agentic RAG](./11_LangGraph/capstone_agentic_rag/)** | S11 extra | LangGraph · RAGAS · Streamlit | Grade → rewrite → groundedness loop → escalate |
| **[Medium Article Agent](./medium-article-agent/)** | S11 extra | LangGraph · FastAPI · React | Ingest PDF/PPTX/HTML → draft → 6 reviewers → HITL → Markdown |
| **[RAG Studio](./10_RAG/capstone_rag_studio/)** | S10 | FastAPI · React · RAGAS · DeepEval | A/B retrieval strategies with numbers, not vibes |
| **[Production RAG chatbot](./10_RAG/notebooks/production_rag_chatbot/)** | S10 | Streamlit · hybrid + rerank | Cited answers over a knowledge base |
| **[RAG chatbot + memory](./10_RAG/notebooks/production_rag_chatbot_memory/)** | S10 / M06 | Streamlit · checkpointer / Store | Multi-turn support bot that remembers |
| **[MCP helpdesk server](./10_RAG/notebooks/production_mcp_agents_rag_capstone/)** | S10 extra | MCP · SQL · RAG | Tools an orchestrator can actually call |
| **[Distill](./05_Local_LLMs_and_API_Providers/distill/)** | S05 | FastAPI · React · Whisper | Classroom assessment; [contribute](https://github.com/nursnaaz/distill/blob/main/CONTRIBUTING.md) |
| **[CineMatch](./01_Text_to_Numbers/movie_recommender/)** | S01 | FastAPI · React | 5 embedders, same 1,000 movies |
| **[Holmes GPT](./03_GPT_Evolution_and_Alignment/holmes_gpt_ui.py)** | S03 | PyTorch · Streamlit | A GPT you trained, not an API wrapper |
| **[Bullish Stock Scanner V3](https://github.com/nursnaaz/TechnicalStockPrediction/tree/feature/v3-high-precision)** | S09 | FastAPI · React · 308 tests | Spec-driven loop engineering in the wild |

---

## 🎮 Classroom presentations (GitHub Pages)

**Do not open the `.html` files from GitHub’s file tree.** They render as source. Use the hosted Pages URLs below (or the [full deck index](https://nursnaaz.github.io/zero-to-genai-engineer/)).

Interactive S00–S02 tutorials live on the instructor site: [nursnaaz.github.io](https://nursnaaz.github.io) (open a tutorial from that homepage).

| Session | Presentation | Link |
|---|---|---|
| S03 | GPT papers (14 slides) | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/03_GPT_Evolution_and_Alignment/GPT_Papers_Presentation.html) |
| S08 | Recap — interactive | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_PRESENTATION.html) |
| S08 | Recap — full text | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/08_Recap/RECAP_SLIDES.html) |
| S10a | Why RAG | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_01_why_rag.html) |
| S10b | Chunking (LangChain) | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_02_ingestion_chunking.html) |
| S10b | Chunking (LlamaIndex) | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_03_ingestion_chunking_llamaindex.html) |
| S10c | Embeddings | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_04_embeddings.html) |
| S10c | Vector databases | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_05_vector_databases.html) |
| S10c | Revision 01–05 | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/revision_notebooks_01_to_05.html) |
| S10d | Why BM25 | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_06_why_bm25.html) |
| S10d | Hybrid search | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_07_why_hybrid.html) |
| S10d | Reranking | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_08_why_reranking.html) |
| S10d | Full pipeline recap | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_09_full_pipeline_recap.html) |
| S10f | Production chatbots / memory | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_11_production_chatbots.html) |
| S10 extra | Multimodal RAG | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/notebooks/teaching_decks/teach_15_multimodal_rag.html) |
| S10 extra | RAG Studio evaluation report | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/10_RAG/capstone_rag_studio/reports/rag_strategy_evaluation_presentation.html) |
| S11a | LangGraph fundamentals | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_01_langgraph_fundamentals.html) |
| S11b | Human-in-the-loop | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_02_human_in_the_loop.html) |
| S11d | Reasoning patterns | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_04_agent_reasoning_patterns.html) |
| S11e | SQL agent | [▶ Open](https://nursnaaz.github.io/zero-to-genai-engineer/11_LangGraph/notebooks/teaching_decks/teach_05_sql_agent.html) |

S11c (multi-agent orchestrator) has no HTML deck — run the [Streamlit app](./11_LangGraph/multi_agent_orchestrator/).

---

## 🛠️ Tech stack (when each tool first appears)

| Purpose | Tools | First used |
|---|---|---|
| Language / notebooks | Python 3.11+ · Jupyter / Colab | Pre-work |
| Classical search | TF-IDF · inverted index | S00 |
| Embeddings | BoW · TF-IDF · Word2Vec · GloVe · FastText · sentence-transformers | S01, S10c |
| Deep learning | PyTorch · TensorFlow/Keras | S02–S03 |
| Tokenisation / sampling | BPE from scratch · tiktoken · temperature / top-k / top-p | S04 |
| Cloud LLMs | OpenAI · Anthropic · Gemini | S04–S07 |
| Local / multi-model | Ollama · LM Studio · OpenRouter · Databricks | S05 |
| Prompt compilers | DSPy (LabeledFewShot · Bootstrap · MIPROv2 · GEPA) | S06 |
| Orchestration | LangChain LCEL · `create_agent` | S07, S10f |
| Vector stores | FAISS · Chroma · Pinecone | S10c |
| Sparse / hybrid | BM25 · SPLADE · RRF | S10d |
| Rerank | Cross-encoder · FlashRank · Cohere | S10d |
| Eval | RAGAS · DeepEval | S10e |
| Memory | Checkpointer · token trim · summarisation · `Store` · condense-question | **S10f (M06)** |
| Agents / graphs | LangGraph · MCP · `create_supervisor` | S10 NB16, S11 |
| UI | Streamlit · FastAPI · React *(selected projects)* | S01+ |

---

## 🧭 Where the 23-module syllabus stands

| Status | Modules |
|---|---|
| ✅ **Shipped in this repo** | **M00–M08 · M10** (sessions **S00–S11**) |
| ✅ **M06 Memory & Chatbots** | Taught inside **S10f + NB13/14** — not a separate weekend |
| ⏸ **M09 LangChain Agents** | ReAct / `ToolNode` / `create_agent` already in **S11a** |
| 🔜 **Still ahead** | CrewAI · deeper MCP productisation · docs/code/multimodal domain apps · FastAPI deploy · LLMOps · guardrails · LoRA · LlamaIndex systems · capstone |

| Module | Topic | Covered in | Status |
|---|---|---|---|
| M00 | Foundations: Search → Text → Transformers → GPT | S00–S03 | ✅ |
| M01 | Tokenization & sampling | S04 | ✅ |
| M02 | Local LLMs & API providers | S05 | ✅ |
| M03 | Prompt engineering + LangChain | S06a/b + S07 | ✅ |
| M04 | MIPROv2 & GEPA | S06c/d | ✅ |
| M05 | Agentic coding & loop engineering | S09 | ✅ |
| **M06** | **Memory & chatbots** | **S10f · NB11 · NB13 · NB14** | ✅ absorbed |
| M07 | RAG basics | S10a–c | ✅ |
| M08 | Production RAG | S10d–g + extras | ✅ |
| M09 | LangChain agents | S11a (`ToolNode` / `create_agent`) | ⏸ inside S11 |
| M10 | LangGraph | S11a–e | ✅ |
| M11 | CrewAI | — | 🔜 |
| M12 | MCP (product / multi-server) | S10 NB16 + S11c start this | 🔜 expand |
| M13 | Document intelligence | S10 ingestion is the start | 🔜 |
| M14 | Code intelligence | — | 🔜 |
| M15 | Multimodal (beyond NB15) | S10 NB15 | 🔜 expand |
| M16 | FastAPI + Docker deploy | Distill / RAG Studio / Medium agent already practice this | 🔜 |
| M17 | LLMOps & evaluation | S10e RAGAS/DeepEval · LangSmith in S10f | 🔜 |
| M18 | Guardrails & safety | S10f + healthcare refusal brief | 🔜 |
| M19 | Fine-tuning (LoRA / QLoRA) | S03 DPO paper is the theory | 🔜 |
| M20 | LlamaIndex knowledge systems | S10b NB03 is the start | 🔜 |
| M21–M22 | Domain + business capstone | 9 RAG group briefs are the rehearsal | 🔜 |

---

<details>
<summary><strong>📅 Session changelog</strong></summary>

<br>

| Date | What shipped |
|---|---|
| 2026-08-23 | **S11d–e** — reasoning patterns + SQL agent. Portfolio: [`medium-article-agent/`](./medium-article-agent/) |
| 2026-08-22 | **S11b–c** — HITL notebook; hierarchical helpdesk orchestrator |
| 2026-08-15 | **S11a** — LangGraph fundamentals & agents |
| 2026-07-19 | S10f–g — production chatbots (memory) + Pinecone showdown |
| 2026-07-18 | S10d–e — hybrid search, reranking, RAGAS, DeepEval |
| 2026-07-05 → 12 | S10a–c — why RAG, chunking, embeddings, vector DBs |
| 2026-06-27 → 28 | S09 — agentic coding & loop engineering |
| 2026-06-20 | S08 recap |
| 2026-06-06 → 13 | S06–S07 — DSPy / GEPA / LangChain |
| 2026-04-03 → 05-10 | Prereq through S05 |

</details>

---

## 🤝 Contributing

Cohort questions go to **WhatsApp**, not Discord. For typos, broken links, or notebook bugs, see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 📄 License

Source code and course materials in this repository are released under the [MIT License](./LICENSE).

---

<div align="center">

*Built with ❤️ by Mohamed Noordeen Alaudeen · AWS GenAI Innovation Center*

⭐ **Star this repo** — it helps other students find it.

Questions? Ask in the **WhatsApp cohort group**.

</div>
