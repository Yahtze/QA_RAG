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

The service boundary is a hard rule. Components must not contain fake timers, fake data generation, or fake error logic. No `setTimeout` in component files. Components call service functions and handle promises. Fake behavior belongs exclusively in `services/`:

- `authService.ts`
- `documentService.ts`
- `chatService.ts`

This keeps backend replacement isolated to service files when real API endpoints exist.

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
3. Service starts fake pipeline.
4. Normal path: `uploading → processing → ready`.
5. Failure path: if `Simulate upload failure` is enabled, pipeline still starts with `uploading`, then transitions to `failed`.
6. Failed document card shows a clear error message and Retry button.
7. Retry restarts the full fake pipeline: `uploading → processing → ready`.

Document card status UI must be visually distinct for each state. The component should accept a `status` prop so external backend events can update it later.

## Chat Flow

Chat behavior:

1. User selects an active ready document.
2. User submits a query.
3. Thread shows the user message immediately.
4. Assistant shows a loading/skeleton state during fake delay.
5. Service returns a deterministic fake answer tied to the active document.
6. Citation panel updates with citations for the latest answer.

Error behavior:

- `Simulate chat error` is a manual debug toggle, not random.
- If enabled, the failed assistant message appears visibly in the thread.
- The error includes a human-readable message and Retry button.
- Retry clears the failed state and resends `ChatError.originalQuery`.

No chat failure should happen silently.

## Citation Panel

The right panel shows placeholder source cards for the latest answer. Cards use realistic attribution such as `Source: page 3` plus snippet text. Citations should be tied to the selected document so the UI feels populated and coherent.

## Simulation Controls

Simulation controls are grouped together and clearly labeled `Simulation controls` or equivalent. They are debug affordances, not production UI.

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
