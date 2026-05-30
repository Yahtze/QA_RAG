# QA RAG

A full-stack RAG (Retrieval-Augmented Generation) application. Upload documents, ask questions, get grounded answers with inline citations — all streamed in real time.

## What It Does

- **Upload** PDF, plain text, and Markdown documents (single or batch)
- **Ingest** documents asynchronously via Celery: text extraction → chunking → embedding → Qdrant vector index
- **Ask questions** against selected documents using a multi-turn conversation interface with full history chaining
- **Retrieve** relevant context via hybrid search: BM25 full-text (Postgres `tsvector`) + semantic similarity (Qdrant vectors), fused with Reciprocal Rank Fusion (RRF)
- **Stream answers** from an LLM via SSE with inline citation labels (`[1]`, `[2]`, etc.)
- **Cite sources** — clickable citation tokens activate source cards showing chunk, document, page, and snippet
- **Cache** semantically similar queries in Redis with vector similarity matching (RediSearch HNSW index)
- **Recover** from failed ingestion via a reconciliation CLI that detects stale/missing states and applies fixes

## Architecture

```
┌──────────────┐     SSE stream      ┌──────────────────────┐
│   Frontend    │◄────────────────────│      Backend         │
│  React + TS   │────────────────────►│    FastAPI (async)   │
│  Vite / nginx │     REST + JWT      │                      │
└──────────────┘                      ├──────────────────────┤
                                      │  Answer Pipeline     │
                                      │  ├─ Lexical (BM25)   │
                                      │  ├─ Semantic (Qdrant)│
                                      │  ├─ RRF Fusion       │
                                      │  ├─ Context Packer   │
                                      │  ├─ History Builder  │
                                      │  ├─ Prompt Builder   │
                                      │  ├─ LLM Stream       │
                                      │  └─ Citation Mapper  │
                                      └─────┬────┬────┬─────┘
                                            │    │    │
                              ┌─────────────┘    │    └──────────────┐
                              ▼                  ▼                   ▼
                        ┌──────────┐      ┌───────────┐       ┌──────────┐
                        │ Postgres │      │   Redis   │       │  Qdrant  │
                        │ (asyncpg)│      │  (cache   │       │ (vectors)│
                        │  data +  │      │  + Celery │       │          │
                        │  chunks  │      │  broker)  │       │          │
                        └──────────┘      └─────┬─────┘       └──────────┘
                                                │
                                          ┌─────▼─────┐
                                          │   Celery   │
                                          │   Worker   │
                                          │ (ingestion)│
                                          └───────────┘
```

### Key Modules

| Module | Responsibility |
|--------|---------------|
| **Session** | JWT auth, register/login/me, redirect guard |
| **Document Pipeline** | Upload → persist file → create DB row → enqueue ingestion |
| **Ingestion** | Extract text → chunk → embed → index in Qdrant → mark ready/failed |
| **Conversation Scope** | Per-conversation active document selection; only active docs participate in RAG. Selection is wired into conversation creation and can be updated mid-conversation. |
| **Hybrid Retrieval** | BM25 + semantic search → RRF rank fusion → top-k context |
| **Answer Pipeline** | Cache check → retrieval → context pack → prompt build (with conversation history) → LLM stream → citation map → persist |
| **Semantic Cache** | Redis vector index cache; bypasses retrieval + LLM on high-similarity hit |
| **Reconciliation** | Detects stale/missing ingestion states; plans and applies recovery actions |

## Quick Start

### Full Stack (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY for embeddings + LLM

# 2. Start everything
make docker-up
```

Services after startup:
- **Frontend**: `http://localhost:8080`
- **Backend API**: `http://localhost:8000`
- **API docs**: `http://localhost:8000/docs`
- **Postgres**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Qdrant**: `localhost:6333`

### Hot Reload Development

```bash
make docker-dev-up
```

Hot reload mode:
- Frontend: Vite dev server on `http://localhost:5173` with source bind mount
- Backend: Uvicorn `--reload` on `http://localhost:8000` with source bind mount
- Worker: shares same backend volume for live code edits

## Local Development (without Docker)

Requires: Python 3.12+, Node 20+, Postgres 16, Redis 7, Qdrant.

```bash
# Backend
cp .env.example .env          # configure DATABASE_URL, REDIS_URL, QDRANT_URL for local services
make backend-install           # install backend into .venv
make backend-migrate           # run Alembic migrations
make backend-dev               # start FastAPI on :8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev   # Vite on :5173

# Worker (separate terminal, if needed)
make backend-worker
```

## Environment Variables

All configuration is via `.env` at the repo root. Copy `.env.example` to start.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | API key for embeddings + LLM (or set `EMBEDDING_BASE_URL`/`LLM_BASE_URL` for OpenRouter etc.) |
| `DATABASE_URL` | `postgresql+asyncpg://qa_rag:qa_rag@localhost:5432/qa_rag` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant connection |
| `JWT_SECRET_KEY` | `dev-secret-change-me-1234567890ab` | JWT signing secret (min 32 bytes for HS256; change in prod) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |
| `EMBEDDING_DIMENSION` | `1536` | Embedding vector dimension |
| `EMBEDDING_BASE_URL` | — | Custom embedding endpoint (OpenRouter, etc.) |
| `LLM_BASE_URL` | — | Custom LLM endpoint |
| `LLM_MODEL` | `gpt-4o-mini` | Chat/answer model |
| `LLM_API_KEY` | falls back to `OPENAI_API_KEY` | LLM-specific API key |
| `USE_ASYNC_INGESTION` | `true` | Use Celery async ingestion (vs. synchronous) |
| `SEMANTIC_CACHE_ENABLED` | `false` | Enable Redis-based semantic cache |
| `SEMANTIC_CACHE_TTL_SECONDS` | `86400` | Cache entry TTL |
| `SEMANTIC_CACHE_MIN_SIMILARITY` | `0.85` | Minimum cosine similarity for cache hit |
| `RETRIEVAL_BM25_TOP_K` | `20` | BM25 candidates per query |
| `RETRIEVAL_SEMANTIC_TOP_K` | `20` | Semantic candidates per query |
| `RETRIEVAL_FINAL_TOP_K` | `8` | Chunks after RRF fusion |
| `CONTEXT_MAX_CHARS` | `12000` | Max context chars sent to LLM |
| `MAX_UPLOAD_BYTES` | `52428800` | Upload size limit (50MB) |
| `STORAGE_ROOT` | `backend/storage` | File upload storage path |

## API Reference

Base URL: `/api/v1`

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT access token |
| `GET` | `/auth/me` | Current user info |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload single document |
| `POST` | `/documents/upload-batch` | Upload multiple documents (207 Multi-Status) |
| `GET` | `/documents` | List documents (cursor pagination) |
| `GET` | `/documents/{id}` | Get document detail |
| `DELETE` | `/documents/{id}` | Hard-delete document (file + vectors + DB) |

Document statuses: `pending` → `processing` → `ready` | `failed`

### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/conversations` | Create conversation |
| `GET` | `/conversations` | List conversations |
| `PUT` | `/conversations/{id}/active-documents` | Set active document IDs for RAG scope |
| `POST` | `/conversations/{id}/messages` | Send message (non-stream, returns full answer) |
| `POST` | `/conversations/{id}/messages/stream` | Send message (SSE stream) |
| `GET` | `/conversations/{id}/messages` | List message history |

### SSE Stream Events

The streaming endpoint emits typed SSE events:

```
event: token
data: {"text": "chunk of answer text"}

event: citations
data: [{"label": "1", "chunk_id": "...", "doc_id": "...", "filename": "...", "page": 2, "snippet": "..."}]

event: done
data: {}

event: error
data: {"message": "...", "retryable": true}
```

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/ready` | Readiness (Postgres + Redis + Qdrant) |

## Frontend

React + TypeScript + Vite with Tailwind CSS and custom UI primitives.

### Key Features

- **3-column layout**: document list (collapsible), chat thread, citation panel (stacked on mobile)
- **Document management**: upload (batch), view status, retry failed, delete
- **Active document selection**: multi-select dialog controls which docs participate in RAG; selection persists to server and flows into conversation creation
- **Multi-turn chat**: full conversation history is chained with each LLM call — prior questions, context chunks, and answers are all passed so the model can reference earlier turns
- **Streaming chat**: real-time token rendering with SSE consumption
- **Citation interaction**: click `[1]` labels in answers to highlight source cards
- **Session persistence**: auth + conversation state survives page refresh
- **New Chat**: resets thread for clean demo flow

### Service Architecture

All async/API behavior lives behind service seams — components never contain fetch logic directly:

```
services/
├── apiClient.ts          # Base HTTP client with JWT auth
├── authService.ts        # Login/register/token
├── documentService.ts    # Upload/list/delete
├── chatService.ts        # Messages/active docs
└── conversationStream.ts # SSE stream consumer
```

Swap these adapters to change backend behavior without touching UI.

## Backend

FastAPI (async) with SQLAlchemy, Alembic, Celery, and deep module seams.

### Key Modules (backend/app/services/)

| File | Purpose |
|------|---------|
| `session.py` | JWT auth service |
| `document_pipeline.py` | Upload orchestration |
| `async_document_upload.py` | Store file + create pending row + enqueue |
| `ingestion_queue.py` | Celery task enqueue seam |
| `ingestion.py` | Extract → chunk → embed → vector store |
| `document_extraction.py` | PDF/text/markdown text extraction |
| `chunking.py` | Deterministic character-based chunking |
| `embeddings.py` | OpenAI-compatible embedding provider seam |
| `vector_store.py` | Qdrant CRUD operations |
| `lexical_retriever.py` | Postgres BM25 full-text search |
| `semantic_chunk_search.py` | Qdrant semantic similarity search |
| `hybrid_retrieval.py` | RRF fusion of BM25 + semantic results |
| `context_packer.py` | Token/char budget packing |
| `prompt_builder.py` | Grounded document assistant prompt with multi-turn history chaining |
| `llm_provider.py` | OpenAI-compatible LLM streaming seam |
| `answer_pipeline.py` | Full RAG orchestration (cache → retrieve → pack → prompt → stream → persist) |
| `semantic_cache.py` | Redis RediSearch HNSW vector cache |
| `citation_mapper.py` | Label → chunk metadata mapping |
| `conversation.py` | Message/citation persistence |
| `conversation_scope.py` | Active document management per conversation |
| `ingestion_reconciliation.py` | Stale state detection + recovery planning |
| `storage.py` | Local file storage seam |
| `readiness.py` | Postgres/Redis/Qdrant health checks |

### Celery Worker

```bash
make backend-worker
```

Processes the `ingestion` queue. Tasks: extract → chunk → embed → index → mark ready/failed. Retry policy: `RetryableIngestionError` keeps document in `processing` (Celery retries); `DeterministicIngestionError` marks `failed` immediately.

### Reconciliation CLI

```bash
# Dry run — shows what would be fixed
make backend-reconcile-ingestion

# Apply fixes
make backend-reconcile-ingestion-apply
```

Detects stale `processing` documents and plans recovery: `MARK_READY`, `MARK_FAILED`, `FULL_REINGEST`.

## Testing

```bash
# Backend tests
make backend-test

# Frontend tests
cd frontend && npm run test

# Linting
make backend-lint
make lint
```

Test strategy:
- **Deep modules are the primary test surface** — service classes, not HTTP routes
- Tests use fake embeddings, fake vector stores, fake LLM providers — no real network calls
- Route tests focus on HTTP mapping, auth, and schema behavior
- Frontend tests cover context/store behavior (session, document pipeline, conversation)

## Make Targets

| Target | Description |
|--------|-------------|
| `make docker-up` | Start full stack |
| `make docker-dev-up` | Start with hot reload |
| `make docker-down` | Stop all services |
| `make docker-logs` | Tail all service logs |
| `make dev` | Frontend dev server only |
| `make backend-dev` | Backend dev server only |
| `make backend-install` | Install backend into .venv |
| `make backend-test` | Run backend test suite |
| `make backend-lint` | Ruff check |
| `make backend-migrate` | Run Alembic migrations |
| `make backend-revision` | Generate new migration (`make backend-revision name="description"`) |
| `make backend-worker` | Start Celery worker |
| `make backend-reconcile-ingestion` | Dry-run ingestion reconciliation |
| `make backend-reconcile-ingestion-apply` | Apply ingestion reconciliation fixes |
| `make lint` | Frontend lint |
| `make build` | Frontend production build |

## Project Structure

```
QA_RAG/
├── frontend/                    # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Base UI primitives
│   │   │   ├── chat/            # Chat thread, input, citations, active docs dialog
│   │   │   ├── documents/       # Upload panel, document list/card
│   │   │   └── layout/          # App shell, top bar, auth guard
│   │   ├── pages/               # Login, Register, Chat
│   │   ├── services/            # API adapters (the seam layer)
│   │   ├── store/               # React contexts (session, docs, conversation, scope)
│   │   └── types/               # Shared TypeScript interfaces
│   ├── Dockerfile               # Multi-stage: node build → nginx serve
│   └── Dockerfile.dev           # Dev image with Vite dev server
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI route handlers
│   │   ├── core/                # Config, database, security
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Deep modules (see table above)
│   │   ├── worker/              # Celery app + tasks
│   │   └── cli/                 # Reconciliation CLI
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite
│   ├── Dockerfile
│   └── pyproject.toml
├── docs/
│   └── superpowers/
│       ├── specs/               # Design specs
│       ├── plans/               # Implementation plans
│       ├── notes/               # Session context notes
│       └── follow-ups/          # Tracked follow-up tickets
├── docker-compose.yml           # Production stack
├── docker-compose.dev.yml       # Dev override (hot reload)
├── Makefile                     # All make targets
├── .env.example                 # Environment variable template
└── AGENTS.md                    # Agent workflow guidelines
```

## Design Decisions

- **Module interfaces are the test boundary** — not HTTP routes. Tests hit service classes directly.
- **Service seams are mandatory** — all async/API behavior lives behind typed interfaces so adapters can be swapped without rewriting UI or route handlers.
- **Chunk text is source of truth in Postgres** — Qdrant holds vectors for similarity search; retrieval joins back to Postgres for text + metadata.
- **Hard filter parity** — Qdrant semantic filters mirror Postgres lexical filters (user_id, active document IDs, status=ready).
- **Streaming persistence** — user message persisted before stream starts; assistant message + citations persisted after stream completes. Crash caveat: dangling user message detected on next load with retry prompt.
- **Multi-turn chaining** — each LLM call receives the full conversation history (user questions + context chunks + assistant answers) with the system prompt at the top. Prior turns' citations are reconstructed from stored citation rows.
- **Active document scope** — multi-select dialog controls which documents participate in RAG. Selection is persisted per-conversation via `PUT /conversations/{id}/active-documents` and passed when creating new conversations.
- **Deterministic test doubles** — fake embeddings, fake vector stores, fake LLMs return predictable outputs for reliable CI.
- **`.env` is source of truth** — Docker Compose reads from `.env` and passes to containers. No hardcoded keys in compose files.
