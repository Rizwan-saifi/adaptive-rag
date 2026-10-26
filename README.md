# Adaptive RAG Platform

A full-stack, agentic Retrieval-Augmented Generation (RAG) chatbot. Users sign in, upload PDF/TXT documents,
and ask questions. Each question is routed to the right strategy: search the uploaded documents, answer from
general knowledge, or search the web.

## Architecture

```
Streamlit UI (:8501)
   │  signup / login                         chat / upload
   ▼                                              │
NestJS BFF (:8080)                                │
   • API-token + JWT auth (Argon2, SQLite)        │
   • /api/chat proxy ─────────────────────────────┤
                                                  ▼
                                  FastAPI RAG service (:8000)
                                     • LangGraph workflow: classify → retrieve → grade → rewrite → generate
                                     • Tool-calling agent over a FAISS vector store
                                     • Web search (Tavily) and general-knowledge routes
                                     • Pluggable LLMs: Groq / OpenAI / Gemini / Anthropic
                                     • Chat history in MongoDB
```

| Folder | Stack | Role |
|---|---|---|
| [`rag-service/`](rag-service/) | Python, FastAPI, LangGraph, LangChain, FAISS, MongoDB, Streamlit | RAG service and web UI |
| [`auth-gateway/`](auth-gateway/) | TypeScript, NestJS, JWT, Argon2, SQLite | Auth gateway (Backend-For-Frontend) |

## Highlights

- **Adaptive routing:** an LLM classifier sends each query to document retrieval, a general-knowledge answer, or web search.
- **Self-correcting retrieval:** retrieved results are graded for relevance; weak results trigger query rewriting and another retrieval pass.
- **Provider-agnostic LLM layer:** switch between Groq, OpenAI, Gemini and Anthropic with one environment variable; embeddings can run locally for free (FastEmbed).
- **Native tool calling:** the retrieval agent uses each provider's tool-calling API rather than text-parsed ReAct.
- **Layered auth:** API tokens plus 1-hour JWTs, with Argon2id password hashing.

## Quick start (Windows)

Prerequisites: Python 3.11+, Node.js 20+, MongoDB running on `localhost:27017`.

```powershell
# RAG service
cd rag-service
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# create rag-service/.env (see below)

# Auth gateway
cd ..\auth-gateway
npm install
npm run build

# Start everything (opens three windows)
cd ..
.\start-all.ps1
```

Open http://localhost:8501, create an account, upload a document and start chatting.

### `rag-service/.env`

```env
LLM_PROVIDER=groq            # groq | openai | gemini | anthropic
EMBEDDING_PROVIDER=local     # local | openai | gemini
GROQ_API_KEY=...             # key for the provider you chose
TAVILY_API_KEY=...           # web search
JWT_SECRET=...               # required; same value as in auth-gateway/.env
```

See [`rag-service/README.md`](rag-service/README.md) for all options, and
[`auth-gateway/README.md`](auth-gateway/README.md) for the auth API.
