# QA RAG

Frontend + backend foundation for QA RAG.

## Backend quick start

```bash
make backend-install
make backend-migrate
make backend-dev
```

Backend: `http://localhost:8000`.
Frontend: `http://localhost:8080` (docker) or `http://localhost:5173` (vite).

## Full stack with Docker

```bash
make docker-up
```

Services: frontend, backend, migrate, postgres, redis, qdrant.

## Full stack with Docker hot reload

```bash
make docker-dev-up
```

Hot reload mode:
- Frontend runs Vite on `http://localhost:5173` with source bind mount.
- Backend runs Uvicorn `--reload` on `http://localhost:8000` with backend bind mount.
- Worker shares same backend/storage volume and code mount for local edits.

## API

- Base: `/api/v1`
- Health: `/health`, `/health/ready`
- Auth: JWT bearer access token only (`/auth/register`, `/auth/login`, `/auth/me`)
- Documents: upload/list/get/delete persisted stubs
- Conversations: create/list/send/list-messages persisted stubs

Upload limit: `MAX_UPLOAD_BYTES` (default 50MB). Types: PDF, text/plain, text/markdown.

## Non-goals (not implemented)

- RAG ingestion/retrieval pipeline
- queues/background workers
- SSE streaming
- refresh tokens
