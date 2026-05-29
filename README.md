# QA RAG

Dockerized React frontend for a QA RAG app with fake auth, document processing, chat answers, and citations.

## Quick start

```bash
docker compose up --build
```

Visit `http://localhost:8080`.

## Local dev

```bash
cd frontend
npm install
npm run dev
```

Vite serves the app at `http://localhost:5173`.

## Environment variables

Copy `.env.example` when backend integration begins. Current frontend uses fake local adapters and does not require environment variables.

## Architecture overview

The frontend lives in `frontend/` and uses React, TypeScript, Vite, Tailwind, and shadcn/ui. Deep modules keep behavior behind seams: Session, Document Pipeline, Conversation, and Simulation Profile. See `docs/superpowers/specs/2026-05-28-qa-rag-frontend-design.md` for the design.

## Current mocked features

- Auth is fake token state.
- Upload and processing are fake async flows.
- RAG answers and citations are deterministic fake data.
- Error controls are deterministic simulation toggles.
- No backend, persistence, embeddings, or real streaming exist yet.

## Project structure

```text
repo-root/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── docs/
├── docker-compose.yml
├── Makefile
├── README.md
└── .env.example
```

## Useful commands

```bash
make dev
make build
make lint
make docker-up
make docker-down
make docker-logs
make clean
```
