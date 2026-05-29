# QA RAG Frontend Design

## Status

Approved design for the initial frontend slice of the QA RAG app.

## Goals

Build a polished, Dockerized frontend for a QA RAG application using React, TypeScript, Vite, Tailwind, and shadcn/ui. The first slice is a functional UI with realistic fake data and fake async service behavior. Backend integration is intentionally stubbed, but the frontend must be structured so real API calls can replace fake services with minimal component changes.

## Repository Structure

```text
repo-root/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/          # shadcn components live here
│   │   │   ├── chat/        # ChatThread, MessageBubble, CitationCard
│   │   │   ├── documents/   # DocumentList, DocumentCard, UploadPanel
│   │   │   └── layout/      # Sidebar, TopBar, AuthGuard
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   └── Chat.tsx
│   │   ├── services/        # Fake API layer now, real fetch calls later
│   │   ├── store/           # React state/context
│   │   └── types/           # Shared TypeScript interfaces
│   ├── Dockerfile
│   ├── nginx.conf
│   └── vite.config.ts
├── docker-compose.yml
├── Makefile
├── README.md
└── .env.example
```

Root is the orchestration layer. `frontend/` owns the Vite React app and static-serving container details.

## Architecture

The app has three routes:

- `/login`
- `/register`
- `/chat`

Authentication is fake but structured like a real app. Login and register set a fake token and navigate to `/chat`. An `AuthGuard` protects `/chat` and redirects unauthenticated users to `/login`. Default redirect logic must live in one place, either the root route handler or `AuthGuard`, not duplicated across pages.

The service seam is a hard rule. Components must not contain fake timers, fake data generation, or fake error logic. No `setTimeout` in component files. Components call module interfaces and handle results. Fake behavior belongs behind deep modules:

- `Session` module, backed first by `authService.ts`
- `Document Pipeline` module, backed first by `documentService.ts`
- `Conversation` module, backed first by `chatService.ts`
- `Simulation Profile` module, backed first by local state/config

This keeps backend replacement isolated to adapters at seams when real API endpoints exist.

## Deep Modules and Seams

The frontend should be organized around deep modules, not thin pass-through wrappers. The interface is the test surface. Use the deletion test: if deleting a module only moves the same complexity into callers, it is shallow and should not exist in that shape.

### Session Module

The `Session` module owns fake authentication state and redirect invariants.

Interface responsibilities:

- expose whether the user is authenticated
- login/register/logout with fake token state
- provide the single redirect decision for root routes and guarded routes

Implementation responsibilities:

- fake token storage for this slice
- fake user data
- future replacement with real auth adapter

Leverage: route guards and pages do not duplicate redirect rules. Locality: fake auth can become real auth by changing one module implementation.

### Document Pipeline Module

The `Document Pipeline` module owns Document upload, status progression, selection, failure, and retry.

Interface responsibilities:

- list seeded and uploaded Documents
- upload a selected file
- select a ready Document
- retry a failed Document
- expose status updates as data callers can render

Implementation responsibilities:

- fake upload delay
- fake processing delay
- deterministic failure when the `Simulation Profile` asks for it
- eventual replacement with backend upload, polling, Redis/Celery completion events, or WebSocket events

Callers must not know pipeline timer details. They render Documents and invoke module operations.

Leverage: tests can verify `uploading → processing → ready` and `uploading → failed → retry → ready` through one interface. Locality: pipeline bugs stay inside one module.

### Conversation Module

The `Conversation` module owns message lifecycle, assistant loading state, failed assistant messages, retry, answers, and Citations.

Interface responsibilities:

- send a query for the active ready Document
- retry a failed query using `ChatError.originalQuery`
- expose the message thread
- expose latest Citations

Implementation responsibilities:

- fake assistant delay
- deterministic fake answer generation tied to the active Document
- deterministic failure when the `Simulation Profile` asks for it
- future replacement with real RAG requests and token streaming

Leverage: one interface exercises success, loading, error, retry, and citation updates. Locality: streaming can be added behind the same seam.

### Simulation Profile Module

The `Simulation Profile` module owns deterministic demo controls.

Interface responsibilities:

- expose `Simulate chat error`
- expose `Simulate upload failure`
- let other modules consume current simulation settings without prop drilling

Implementation responsibilities:

- local UI-controlled state for this slice
- no random failures

Leverage: tests and demos can force exact failure paths. Locality: debug behavior remains separate from production-facing modules.

### Domain Result Shapes

Shared TypeScript types are not enough by themselves. Add small domain result shapes or constructors only when they hide invariants, not as pass-through wrappers. Good candidates include ready documents, failed messages, and citation sets when they prevent impossible UI states.

## Types

Shared interfaces live in `frontend/src/types/`.

Core types:

```ts
type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed'

interface ChatError {
  message: string
  retryable: boolean
  originalQuery?: string
}
```

`DocumentStatus` must be a TypeScript union type, not an enum. Other shared types include `User`, `Document`, `Message`, and `Citation`. Types should be reused by components, store, and services.

## Chat Page Layout

`/chat` uses a responsive three-column layout:

- Left column: upload panel and document list
- Center column: chat thread, input box, send button, and simulation controls
- Right column: citation/source panel

Desktop uses three columns. Mobile stacks the sections vertically.

## Document Flow

Initial load includes realistic seeded documents, with at least:

- one `ready` document
- one `processing` document
- one `failed` document

Upload behavior:

1. User selects a file.
2. Upload button becomes enabled.
3. `Document Pipeline` starts fake pipeline.
4. Normal path: `uploading → processing → ready`.
5. Failure path: if `Simulation Profile` has `Simulate upload failure` enabled, pipeline still starts with `uploading`, then transitions to `failed`.
6. Failed document card shows a clear error message and Retry button.
7. Retry calls `Document Pipeline` and restarts the full fake pipeline: `uploading → processing → ready`.

Document card status UI must be visually distinct for each state. The component should accept a `status` prop so external backend events can update it later. Components must not own status ordering rules.

## Chat Flow

Chat behavior:

1. User selects an active ready document.
2. User submits a query through the `Conversation` module.
3. Thread shows the user message immediately.
4. Assistant shows a loading/skeleton state during fake delay.
5. `Conversation` returns a deterministic fake answer tied to the active document.
6. Citation panel updates from latest `Conversation` citations.

Error behavior:

- `Simulate chat error` is a manual debug toggle, not random.
- If enabled through the `Simulation Profile`, the failed assistant message appears visibly in the thread.
- The error includes a human-readable message and Retry button.
- Retry calls `Conversation` with `ChatError.originalQuery`; the module clears failed state and resends the query.

No chat failure should happen silently.

## Citation Panel

The right panel shows placeholder source cards for the latest answer. Cards use realistic attribution such as `Source: page 3` plus snippet text. Citations should be tied to the selected document so the UI feels populated and coherent.

## Simulation Controls

Simulation controls are grouped together and clearly labeled `Simulation controls` or equivalent. They are debug affordances, not production UI. Controls should write to the `Simulation Profile` module; upload and chat modules consume that interface rather than receiving scattered debug props.

Controls:

- `Simulate chat error`
- `Simulate upload failure`

Both are deterministic toggles. No random error behavior.

## Styling and Components

Use Tailwind for all layout, spacing, typography, and color. Use a dark-only theme with a cohesive CSS variable palette defined up front.

Use shadcn/ui via CLI-installed source components in `frontend/src/components/ui`. Install exactly this set and nothing more:

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

Visual target: polished SaaS RAG product, not a plain homework interface.

## Docker

Create `frontend/Dockerfile` with two stages:

1. Build stage:
   - Node image
   - install dependencies
   - run `npm run build`
   - produce `dist`
2. Serve stage:
   - lightweight Nginx image
   - copy `dist`
   - serve static files

Create `frontend/nginx.conf` with React Router support:

```nginx
try_files $uri $uri/ /index.html;
```

Create root `docker-compose.yml` with one service:

- service name: `frontend`
- build context: `./frontend`
- port mapping: `8080:80`

The compose file is intentionally simple and ready for future backend services.

## Developer Experience

Root `Makefile` targets:

```makefile
make dev
make build
make docker-up
make docker-down
make docker-logs
make lint
make clean
```

README requirements:

- one-line project description at top
- Quick start first: `docker compose up --build`, then visit `localhost:8080`
- Local dev section: `npm install`, `npm run dev`
- Environment variables section referencing `.env.example`
- Architecture overview with link to this design doc
- Project structure tree
- Honest note that auth, upload, RAG answers, citations, and processing are currently mocked

Create `.env.example` for future backend API configuration.

## Testing and Verification

Minimum verification after implementation:

- `npm run lint`
- `npm run build`
- `docker compose up --build` serves app at `localhost:8080`
- Direct route refresh works for `/chat` due to Nginx `try_files`
- Unauthenticated `/chat` redirects to `/login`
- Login/register redirect to `/chat`
- `Session` module tests cover single redirect decision path
- `Document Pipeline` module tests cover Ready and Failed/Retry paths through its interface
- `Conversation` module tests cover answer, citations, failure, and retry through its interface
- `Simulation Profile` module or integration tests cover deterministic failure controls
- Upload success path reaches Ready
- Upload failure path shows Failed and Retry reaches Ready
- Chat success path shows answer and citations
- Chat error path shows failed thread message and Retry resends original query

## Scope Boundaries

In scope:

- frontend app scaffold
- fake auth
- fake document pipeline
- fake RAG chat
- fake citations
- Dockerized static serving
- README, Makefile, env example

Out of scope:

- real backend API
- real file persistence
- real embeddings
- real streaming tokens
- real auth/session persistence beyond fake token state
