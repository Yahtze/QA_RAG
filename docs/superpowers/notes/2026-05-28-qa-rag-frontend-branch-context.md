# QA RAG Frontend Branch Context

## Purpose

This branch starts the frontend for a QA RAG application. The first implementation target is a polished, Dockerized React + TypeScript + Vite UI with realistic fake data and fake async flows. Backend services do not exist yet, so all API behavior is stubbed behind a service layer.

Primary spec: `docs/superpowers/specs/2026-05-28-qa-rag-frontend-design.md`.

## Major Decisions

### Repository Layout

Use a single frontend app under `frontend/`, with root-level orchestration files.

Planned structure:

```text
repo-root/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   └── layout/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── docker-compose.yml
├── Makefile
├── README.md
└── .env.example
```

Reason: keeps repo ready for future backend services while keeping frontend simple and isolated.

### Service Seam Is Mandatory

All fake async behavior belongs behind deep module interfaces, with initial adapters in `frontend/src/services/`.

Do not put `setTimeout`, fake data generation, fake upload pipelines, or fake error logic inside React components. Components should call typed module interfaces and render results. This is the most important architecture rule for future backend wiring.

Expected deep modules and first adapters:

- `Session` module backed by `authService.ts`
- `Document Pipeline` module backed by `documentService.ts`
- `Conversation` module backed by `chatService.ts`
- `Simulation Profile` module backed by local UI-controlled state/config

When backend exists, agents should replace adapters at seams with real fetch/polling/streaming implementations, not rewrite components.

### Types First

Shared interfaces live in `frontend/src/types/` and are reused by services, store, and components.

Important type decision:

```ts
type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed'
```

Use a union type, not an enum.

`ChatError` should preserve retry context:

```ts
interface ChatError {
  message: string
  retryable: boolean
  originalQuery?: string
}
```

`originalQuery` lets Retry resend the exact failed prompt.

### Session Module

Use React Router with fake auth.

Routes:

- `/login`
- `/register`
- `/chat`

Unauthenticated users hitting `/chat` redirect to `/login`. Login/register set a fake token in state and redirect to `/chat`. Default redirect logic should live in one place inside the `Session` module or its route-facing interface, not duplicated across pages.

Architecture vocabulary: `Session` is a Module. Its Interface is the auth and redirect decision surface. Its Implementation is fake-token state now, real auth later.

### Chat UI Scope

Build a full RAG-style UI, not just a bare chat box.

Required areas:

- upload panel
- document list
- chat thread
- chat input/send button
- citation/source panel
- login/register pages
- simulation controls

Layout: 3-column desktop, stacked mobile.

### Document Pipeline Module

Upload flow should mimic real backend stages:

1. `uploading`
2. `processing`
3. `ready`

Failure flow is deterministic through a debug toggle:

1. `uploading`
2. `failed`

Failed document cards need clear error text and Retry. Retry must restart the full fake pipeline through `uploading → processing → ready`.

Reason: real backend will likely map Processing to Celery/queue work and Ready to embedding completion.

Architecture vocabulary: `Document Pipeline` is a deep Module. Its Interface owns upload, list, select, retry, and status updates. Its Implementation owns timers now and backend polling/events later.

### Conversation Module

Send flow:

1. User message appears immediately.
2. Assistant loading/skeleton state appears during fake delay.
3. Service returns deterministic fake answer tied to active document.
4. Citation panel updates with source cards.

Error flow is deterministic through the `Simulation Profile`. Failed assistant message must appear visibly in the thread with human-readable error and Retry. Retry should clear the error and resend `ChatError.originalQuery`.

Architecture vocabulary: `Conversation` is a deep Module. Its Interface owns send, retry, message thread, and latest Citations. Its Implementation owns fake assistant delay now and real RAG/streaming later.

### Simulation Profile Module

Use manual debug toggles only. No random failures.

Controls:

- `Simulate chat error`
- `Simulate upload failure`

Group them clearly under a label like `Simulation controls`, so reviewers understand these are demo/dev controls.

Architecture vocabulary: `Simulation Profile` is a Module. Its Interface exposes deterministic failure settings. Its Implementation is local state/config for this slice.

### Styling and UI Components

Use Tailwind CSS plus shadcn/ui.

Dark-only theme. No light mode needed for this slice.

Install exactly these shadcn components and nothing extra:

- button
- input
- textarea
- dialog
- toast
- skeleton
- badge
- scroll-area
- separator
- avatar
- card
- label
- progress

Goal: polished SaaS product feel, not generic homework UI.

### Docker and Nginx

Frontend must be Dockerized with a multi-stage Dockerfile:

1. Node build stage installs deps and runs `npm run build`.
2. Nginx serve stage copies `dist` and serves static files.

Root `docker-compose.yml` should define one service now:

- service: `frontend`
- build: `./frontend`
- ports: `8080:80`

Nginx config must include React Router fallback:

```nginx
try_files $uri $uri/ /index.html;
```

Without this, refreshing `/chat` will 404 in Docker.

### Developer Experience

Add root `Makefile` targets:

- `make dev`
- `make build`
- `make docker-up`
- `make docker-down`
- `make docker-logs`
- `make lint`
- `make clean`

README should start with quick start, then local dev, environment variables, architecture overview, and project structure. Be honest that auth, upload, RAG answers, citations, and processing are mocked.

## Implementation Notes for Future Agents

- Do not bypass module interfaces for convenience.
- Keep UI modules small and grouped by domain: `chat`, `documents`, `layout`, `ui`.
- Seed fake data so the app looks populated on first launch.
- Make all async demo behavior deterministic for reliable demos and tests.
- Use `DocumentStatus` prop-driven rendering so backend events can update status later.
- Keep `/chat` protected by the `Session` module's redirect decision.
- Verify direct route refresh in Docker after implementation.
- Prefer editing adapters behind seams when changing fake behavior.
- Avoid over-installing shadcn components beyond the approved list.
- Apply the deletion test: if a Module is just passing values through, deepen it or remove it.
- Treat each Module Interface as the test surface.

## Verification Checklist

After implementation, verify:

- `npm run lint`
- `npm run build`
- `docker compose up --build`
- app available at `http://localhost:8080`
- `/chat` redirects to `/login` when unauthenticated
- login/register redirect to `/chat`
- direct refresh on `/chat` works in Docker
- `Session` module tests cover auth redirect behavior
- `Document Pipeline` module tests cover Ready and Failed/Retry paths
- `Conversation` module tests cover answer, citations, failure, and retry
- `Simulation Profile` deterministic controls drive failure paths
- upload success path reaches Ready
- upload failure path shows Failed and Retry reaches Ready
- chat success path shows answer and citations
- chat error path shows failed thread message and Retry resends original query
