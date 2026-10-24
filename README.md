# 🎙️ MediaNova — Autonomous Media Intelligence Platform

<p align="center">
  ⚡ Multi-Agent AI that turns any podcast, video or transcript into summaries, highlights, social content & direct answers
</p>

---
<p align="center">
  <img src="https://media.giphy.com/media/3oKIPEqDGUULpEU0aQ/giphy.gif" width="700" />
</p>

## 🧩 Tech Badges

<p align="center">
  <img src="https://img.shields.io/badge/AI-Multi--Agent-blueviolet"/>
  <img src="https://img.shields.io/badge/LLM-Groq%20GPT--OSS--120B-orange"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue"/>
  <img src="https://img.shields.io/badge/Streamlit-Frontend-red"/>
  <img src="https://img.shields.io/badge/LangGraph-Agent%20Orchestration-green"/>
  <img src="https://img.shields.io/badge/LangChain-Framework-yellow"/>
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-darkgreen"/>
  <img src="https://img.shields.io/badge/RAG-Vector%20%2B%20BM25-purple"/>
  <img src="https://img.shields.io/badge/RAGAS-RAG%20Evaluation-crimson"/>
  <img src="https://img.shields.io/badge/Langfuse-Observability-teal"/>
</p>

---

## 📌 Project Overview

**MediaNova** is a multi-agent media assistant built with LangGraph.

Instead of a single LLM call, it routes every user request through a **Supervisor → Specialist** agent system — intelligently deciding whether to summarize, extract highlights, generate social content, or answer a direct question.

It combines Groq inference, vector-first ChromaDB retrieval supplemented by BM25, a LangChain tool registry, optional Langfuse tracing and RAGAS evaluation, and YouTube transcript ingestion in a session-aware Streamlit app.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| ⚡ **Groq Inference** | Groq-hosted `openai/gpt-oss-120b` model |
| 🧠 **Multi-Agent Pipeline** | Supervisor routes to Summarize / Highlight / Social / Q&A agent |
| 📺 **YouTube Ingestion** | Paste any YouTube URL — transcript fetched, indexed, answered |
| 🔍 **Transcript Retrieval** | ChromaDB vector search, with BM25 results appended when they add distinct chunks |
| 🔧 **Tool Registry** | LangChain tools for Wikipedia, DuckDuckGo, YouTube Transcript, and file reading; per-agent access control (not a standalone MCP server) |
| 💬 **Multi-Session Chat** | Full session history, auto-titles, session switching, export to markdown |
| 💬 **Direct Q&A Mode** | Ask any question — Q&A Agent answers in 2–5 sentences, grounded in context |
| 🛡️ **Guardrails** | Input validation, content moderation, output sanitization, transcript injection filtering |
| 📊 **RAGAS Auto-Evaluation** | Reference-free Faithfulness, Answer Relevancy, and Context Precision |
| 🔭 **Langfuse Observability** | Pipeline, LLM, tool, and evaluation-score tracing |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python 3.11+ | Core programming |
| ⚡ Groq API | LLM inference (`openai/gpt-oss-120b`) |
| 🧠 LangGraph | Agent orchestration (StateGraph) |
| 🔗 LangChain | LLM integration + tool binding |
| 🎨 Streamlit | Frontend UI + multi-session chat |
| 📦 ChromaDB | Persistent vector store |
| 📊 BM25 (rank_bm25) | Keyword retrieval to supplement vector results |
| 🤗 all-MiniLM-L6-v2 | Local embeddings — zero API cost |
| 🌐 DuckDuckGo DDGS | Live web search tool |
| 📖 Wikipedia API | Factual enrichment tool |
| 📊 RAGAS 0.4.3 | Reference-free RAG evaluation and scoring |
| 🔭 Langfuse v5+ | LLM observability + score tracking |
| 🐳 Docker | Containerised production build |

---

## 🏗️ System Architecture

```
MediaNova
│
├── app.py              # Streamlit UI — multi-session chat, source management
├── agent.py            # LangGraph multi-agent pipeline + evaluation trigger
├── rag.py              # Vector-first retrieval with BM25 supplementation
├── evaluation.py       # RAGAS evaluation service (fire-and-forget, non-blocking)
├── mcp_tools.py        # LangChain tool registry (not a standalone MCP server)
├── llm.py              # Groq LLM client (3 temperature modes)
├── prompts.py          # All LLM prompts — ChatPromptTemplate + Few-Shot + CoT
├── guardrails.py       # Input validation, content moderation, output sanitization
├── tracer.py           # Langfuse observability wrapper
├── schemas.py          # Pydantic v2 schemas for I/O validation
├── config.py           # Central config — models, RAG params, eval thresholds
├── Dockerfile          # Multi-stage production build
├── docker-compose.yml  # Local dev + persistent volumes
├── requirements.txt
├── .env                # API keys (NOT pushed to GitHub)
└── README.md
```

---

## 🤖 Agent Pipeline

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                    Supervisor Node                    │
│          Reads query, decides routing (temp=0.0)      │
└────┬──────────┬──────────────┬────────────────────────┘
     │          │              │              │
     ▼          ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐  ┌────────────┐
│Summarize│ │Highlight│ │ Social  │  │  Q&A Agent │
│  Agent  │ │  Agent  │ │  Agent  │  │            │
└────┬────┘ └────┬────┘ └────┬────┘  └─────┬──────┘
     │           │           │             │
     ▼           ▼           ▼             ▼
 Wikipedia   Wikipedia   Web Search      No tools
 Web Search  Web Search    (only)         (Q&A)
     │           │           │             │
     ▼           ▼           ▼             ▼
  Groq 0.3   Groq 0.0    Groq 0.75    Groq 0.3
 (balanced) (precise)   (creative)   (balanced)
     │           │           │             │
     └───────────┴───────────┴─────────────┘
                         │
                         ▼
              Output Guardrails
              (validation + sanitization)
                         │
                         ▼
                 Final Response → UI
                         │
                         ▼ (background daemon thread)
              RAGAS Evaluation (non-blocking)
                         │
                         ▼
              Langfuse scores (when authenticated)
```

### 🤖 Agent Routing Logic

| Query type | Example | Routes to |
|---|---|---|
| Wants a summary / overview | "summarize this video" | `summarize_agent` |
| Wants highlights / key moments | "what are the key points?" | `highlight_agent` |
| Wants social media content | "write a LinkedIn post" | `social_agent` |
| Asks a direct question | "what does X mean?" / "who is Y?" | `qa_agent` |

> **Routing behavior:** The structured LLM router classifies intent; the keyword fallback uses question words as one signal for `qa_agent`. Q&A uses transcript context and has no external tools.

---

## 🔍 Transcript Retrieval

```
User Query
    │
    ├──────────────────────────────┐
    ▼                              ▼
ChromaDB vector search
(semantic similarity; selected first)
               │
               ├── BM25 keyword results
               │   appended if distinct
               ▼
      Deduplicate, vector-first,
         then truncate to top_k
               │
               ▼
  retrieve_context_with_chunks()
  returns: (joined_str, List[str])
       │              │
       ▼              ▼
   LLM Prompt    RAGAS Evaluation
```

> This is vector-first supplementation, not weighted 60/40 fusion. `BM25_WEIGHT` and `VECTOR_WEIGHT` are not used by the current merge logic. If vector results already fill `top_k` with distinct chunks, BM25 adds none to the final context.

---

## 📊 RAGAS Evaluation Pipeline

MediaNova evaluates production queries with reference-free **RAGAS 0.4.3** in a background thread.

```
run_agent() completes
       │
       ▼ (fire-and-forget daemon thread — user never waits)
EvaluationService.evaluate_fire_and_forget()
       │
       ▼
_run_ragas_sync()
  ├── Faithfulness                          (is answer grounded in context?)
  ├── Answer Relevancy                      (does answer address the question?)
  └── LLMContextPrecisionWithoutReference   (is retrieval pulling clean chunks?)
       │
       ▼
_check_thresholds()  →  WARNING logs + UI alerts if below threshold
       │
       ▼
tracer.score_response()  →  client.create_score()  →  Langfuse dashboard
```

### Evaluation Metrics

| Metric | What it measures | Threshold |
|---|---|---|
| **Faithfulness** | Is the answer grounded in retrieved context? Low = hallucination risk | `>= 0.70` |
| **Answer Relevancy** | Does the answer actually address the query? | `>= 0.65` |
| **Context Precision** | Are retrieved chunks mostly relevant? Low = noisy retrieval | `>= 0.60` |
| **Hallucination Score** | Derived: `1 - faithfulness`. High = fabrication risk | `<= 0.30` |

> All metrics are **reference-free** — no ground truth needed. Evaluation scores are posted to Langfuse when score logging is enabled and credentials are configured.

---

## 🔭 Langfuse Observability

MediaNova traces pipeline runs with **Langfuse v5+**:

| What is traced | Langfuse object |
|---|---|
| Full pipeline run | Root span (`medianova_pipeline`) |
| Supervisor routing decision | Child span |
| RAG retrieval | Child span (chunk count + latency; no transcript text) |
| Every LLM call (LangGraph) | Auto-traced via `CallbackHandler` |
| Tool calls | Child tool spans (input + result size) |
| Social post approval | Child agent span on the original trace |
| RAGAS scores | `create_score()` per metric, when evaluation and Langfuse auth succeed |
| User thumbs up / down | `create_score("user_feedback")` |

> **Trace context:** Runs are grouped under the Streamlit session; callbacks and approval resumes link to the trace ID.
>
> **Data notice:** LangChain callbacks record LLM prompts and outputs in Langfuse; prompts can include retrieved transcript text. Do not submit sensitive transcripts if your Langfuse project is not approved to store them.

---

## 🛡️ Production Guardrails

Three-layer protection on every request:

```
Input Query
    │
    ▼
1. Pydantic QueryInput validation
   (min/max length, whitespace, injection patterns)
    │
    ▼
2. Content moderation
   (off-topic, harmful, ambiguous — rule-based, no API cost)
    │
    ▼
3. Output guardrails
   (HighlightOutput schema validation, prompt-leak sanitization)
```

---

## 🔧 LangChain Tool Registry

| Tool | Description | Agent Access |
|---|---|---|
| `youtube_transcript` | Fetches transcript from YouTube URL | App-level ingestion; no active graph agent access |
| `web_search` | Live DuckDuckGo search | Summarize, Highlight, Social |
| `wikipedia_search` | Factual background on people & topics | Summarize, Highlight |
| `read_file` | Reads local .txt / .srt / .md transcript | Registered, but no active graph agent access |

> These are LangChain tools in a local registry, not a standalone MCP server. The `research_agent` access entry has no corresponding node in the active graph; Q&A has no tools.

---

## ⚙️ Installation Guide

### 1️⃣ Clone Repository

```bash
git clone https://github.com/tejasrastogileet/m.git
cd m
```

### 2️⃣ Create Virtual Environment

Python 3.12 is recommended on Windows for the available dependency wheels.

```bash
py -3.12 -m venv .venv312
source .venv312/Scripts/activate   # Git Bash
# PowerShell: .\.venv312\Scripts\Activate.ps1
```

### 3️⃣ Install Dependencies

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create `.env` in the project root. Never commit this file or share its secret values.

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional: Langfuse observability (v5+ SDK); use the host for your project region
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
LANGFUSE_TRACING_ENVIRONMENT=development

# Optional: background RAGAS evaluation and score posting
EVAL_ENABLED=true
EVAL_LOG_TO_LANGFUSE=true
EVAL_THRESH_FAITHFULNESS=0.70
EVAL_THRESH_PRECISION=0.60
EVAL_THRESH_RELEVANCY=0.65
EVAL_THRESH_HALLUCINATION=0.30
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)  
Get your Langfuse keys at [cloud.langfuse.com](https://cloud.langfuse.com)

### 5️⃣ Run the App

```bash
python -m streamlit run app.py
```

Index a transcript in **Manage content source** before asking questions to populate vector and BM25 retrieval.

### 6️⃣ Run Evaluations

```bash
python eval_routing.py
python eval_injection.py
```

### 🐳 Run with Docker

```bash
docker compose up --build    # first run
docker compose up            # subsequent runs
docker compose down -v       # stop + wipe volumes
```

---

## Routing Evaluation

`eval_data.json` contains 60 manually authored queries (15 per agent), including 20 hard examples missed by `keyword_route`; `eval_routing.py` shuffles with seed 42 and splits 50/50.

| Router | Dev accuracy (30) | Test accuracy (30) |
|---|---:|---:|
| Keyword fallback | 66.67% | 66.67% |
| Groq structured LLM | Not re-verified (requires Groq API key) | Not re-verified (requires Groq API key) |

> The keyword figures are from a small, manually authored benchmark, not an independent production evaluation. Structured-router accuracy is not verified in the current environment; rerun with a valid Groq API key before reporting its score.

## Human-in-the-Loop

1. Social-agent drafts reach an approval node, which calls `interrupt({"draft": state["response"]})`.
2. `MemorySaver` checkpoints the graph under the session's `thread_id` while it waits.
3. Approve/Reject resumes that same thread with `Command(resume={...})`; only social-agent drafts pause.

## Limitations

- `MemorySaver` is in-memory; pending approvals do not survive process restarts.
- The routing evaluation set is small (60 examples); measured accuracy may not generalize.
- Human approval currently applies only to the social agent.
- No automated test suite or CI workflow is configured in the repository.

## Prompt-Injection Evaluation

`eval_injection.py` checks 15 poisoned and 15 clean transcript snippets. Current rules block 100% of the poisoned samples with 0% false positives on this small set.

## Project Verification

Verified locally with Python 3.12: keyword routing evaluation on the 60-query working-tree dataset, prompt-injection filtering evaluation, and syntax checks. Structured Groq routing requires a valid API key.

---

## 🧠 How It Works

```
1️⃣  User sends a query (or pastes a YouTube URL)
        │
2️⃣  Input guardrails → Pydantic validation + content moderation
        │
3️⃣  YouTube URL detected? → Fetch transcript → Clear ChromaDB → Re-index
        │
4️⃣  retrieve_context_with_chunks() → vector-first ChromaDB results, supplemented by distinct BM25 matches
        │                              returns both joined string AND raw list
        │
5️⃣  Supervisor reads query → Routes to Summarize / Highlight / Social / Q&A agent
        │        (question words detected? → qa_agent for direct concise answer)
        │
6️⃣  Summarize / Highlight / Social agents may call permitted LangChain tools via ReAct; Q&A uses no tools
        │
7️⃣  Agent formats prompt → Groq LLM → Output guardrails → Response to UI
        │
8️⃣  If enabled: background RAGAS evaluation for faithfulness + relevancy + precision
        │         Scores may be posted if evaluation and Langfuse authentication succeed
        │
9️⃣  Response rendered in chat — markdown or styled highlight cards
       User can submit 👍/👎 feedback → score_response("user_feedback") → Langfuse
```

---

## 📚 What I Learned

✔ **LangGraph StateGraph** — building real state machines with typed state and conditional edges  
✔ **Vector-first Retrieval** — ChromaDB results supplemented by distinct BM25 matches
✔ **LangChain Tool Registry** — per-agent access control, tool binding, ToolMessage conversations (not an MCP server)
✔ **Multi-Session State Management** — Streamlit session_state design for complex apps  
✔ **Persistent RAG Storage** — ChromaDB PersistentClient and real-time re-indexing
✔ **LLM Temperature Strategy** — precise / balanced / creative modes for different task types  
✔ **YouTube API Integration** — youtube-transcript-api v1.x, URL parsing, live ingestion  
✔ **Intelligent Task Routing** — keyword-based intent detection to separate Q&A from generation tasks  
✔ **RAGAS Evaluation** — reference-free Faithfulness, Relevancy, and Context Precision scores
✔ **Langfuse Observability** — trace-context-aware tracing, callbacks, spans, and evaluation scores
✔ **Production Guardrails** — Pydantic v2 input/output validation, prompt injection detection, content moderation  
✔ **SDK Version Debugging** — diagnosed breaking changes across RAGAS 0.1→0.4 and Langfuse v2→v5 APIs  

---

## 🎯 Future Improvements

🔹 Cross-encoder reranking — add `cross-encoder/ms-marco-MiniLM-L-6-v2` between retrieval and TOP-K slice  
🔹 Semantic chunking — replace character splitter with `SemanticChunker` for boundary-aware chunks  
🔹 Offline CI evaluation — RAGAS batch evaluation against collected JSONL dataset in GitHub Actions  
🔹 Speaker diarization — identify who said what in transcripts  
🔹 Multi-turn Q&A — follow-up questions that remember previous answers in session  
🔹 Multi-document RAG — index multiple videos/files simultaneously  
🔹 Audio file support — direct .mp3/.wav upload with Whisper transcription  
🔹 Synthetic dataset generation — RAGAS testset generator for automated benchmark creation  

---

## 👨‍💻 Author

**Tejas Rastogi**

🔗 GitHub: [github.com/tejasrastogileet](https://github.com/tejasrastogileet)

---

## ⭐ Support

If you like this project:

⭐ **Star the repository**  
📢 **Share with others**  
🍴 **Fork and build on top of it**

---

## 📢 Tags

`AI` `Multi-Agent` `LangGraph` `LangChain` `Groq` `RAG` `ChromaDB` `BM25` `Streamlit` `YouTube` `Tool Registry` `RAGAS` `Langfuse` `Evaluation` `Observability` `Guardrails` `Python` `Generative AI` `LLM` `Docker`
