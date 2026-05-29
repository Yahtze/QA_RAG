# QA RAG Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first QA RAG frontend slice: Dockerized Vite React TypeScript app with fake auth, Document Pipeline, Conversation, Citations, Simulation Profile, Tailwind/shadcn UI, README, Makefile, and verification.

**Architecture:** `frontend/` owns the app. Deep Modules expose small interfaces: `Session`, `Document Pipeline`, `Conversation`, and `Simulation Profile`; initial adapters use fake async services. UI modules render state and call module interfaces only. No `setTimeout` or fake data generation in React UI files.

**Tech Stack:** React, TypeScript, Vite, React Router, Tailwind CSS, shadcn/ui, Vitest, Testing Library, Docker, Nginx, docker compose.

---

## File Map

Create/modify these files:

- Root:
  - `docker-compose.yml` — compose service for frontend on `8080:80`.
  - `Makefile` — dev/build/docker/lint/clean commands.
  - `README.md` — quick start, local dev, env, architecture, project tree, mocked status.
  - `.env.example` — future frontend env values.
- Frontend config:
  - `frontend/package.json` — scripts and dependencies.
  - `frontend/index.html` — Vite entry.
  - `frontend/vite.config.ts` — React/Vitest/path alias config.
  - `frontend/tsconfig.json`, `frontend/tsconfig.node.json` — TypeScript config.
  - `frontend/tailwind.config.ts`, `frontend/postcss.config.js` — Tailwind config.
  - `frontend/components.json` — shadcn config.
  - `frontend/eslint.config.js` — lint config.
  - `frontend/Dockerfile` — Node build, Nginx serve.
  - `frontend/nginx.conf` — static serving + React Router fallback.
- Frontend source:
  - `frontend/src/main.tsx` — React bootstrap.
  - `frontend/src/App.tsx` — providers + routes.
  - `frontend/src/index.css` — Tailwind layers + dark SaaS palette.
  - `frontend/src/lib/utils.ts` — `cn` helper.
  - `frontend/src/types/index.ts` — shared domain types.
  - `frontend/src/services/authService.ts` — fake auth adapter.
  - `frontend/src/services/documentService.ts` — fake Document Pipeline adapter.
  - `frontend/src/services/chatService.ts` — fake Conversation adapter.
  - `frontend/src/store/SessionContext.tsx` — Session Module interface/provider.
  - `frontend/src/store/SimulationProfileContext.tsx` — Simulation Profile Module.
  - `frontend/src/store/DocumentPipelineContext.tsx` — Document Pipeline Module.
  - `frontend/src/store/ConversationContext.tsx` — Conversation Module.
  - `frontend/src/components/layout/AuthGuard.tsx` — route guard.
  - `frontend/src/components/layout/AppShell.tsx` — 3-column responsive shell.
  - `frontend/src/components/layout/TopBar.tsx` — header/logout.
  - `frontend/src/components/layout/SimulationControls.tsx` — deterministic toggles.
  - `frontend/src/components/documents/UploadPanel.tsx` — file input/upload.
  - `frontend/src/components/documents/DocumentList.tsx` — list wrapper.
  - `frontend/src/components/documents/DocumentCard.tsx` — status card/retry/select.
  - `frontend/src/components/chat/ChatThread.tsx` — scrollable messages.
  - `frontend/src/components/chat/MessageBubble.tsx` — user/assistant/error/loading bubble.
  - `frontend/src/components/chat/ChatInput.tsx` — input/send.
  - `frontend/src/components/chat/CitationCard.tsx` — source card.
  - `frontend/src/components/chat/CitationPanel.tsx` — latest citations.
  - `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`, `frontend/src/pages/Chat.tsx`.
  - `frontend/src/test/setup.ts` — test setup.
- shadcn UI source:
  - `frontend/src/components/ui/*` generated via shadcn CLI for exactly approved components.
- Tests:
  - `frontend/src/store/__tests__/SessionContext.test.tsx`
  - `frontend/src/store/__tests__/DocumentPipelineContext.test.tsx`
  - `frontend/src/store/__tests__/ConversationContext.test.tsx`
  - `frontend/src/App.test.tsx`

---

### Task 1: Scaffold Vite React TypeScript app

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/eslint.config.js`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Create package and config files**

Create `frontend/package.json`:

```json
{
  "name": "qa-rag-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "class-variance-authority": "latest",
    "clsx": "latest",
    "lucide-react": "latest",
    "react": "latest",
    "react-dom": "latest",
    "react-router-dom": "latest",
    "tailwind-merge": "latest",
    "tailwindcss-animate": "latest"
  },
  "devDependencies": {
    "@eslint/js": "latest",
    "@testing-library/jest-dom": "latest",
    "@testing-library/react": "latest",
    "@testing-library/user-event": "latest",
    "@types/node": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "autoprefixer": "latest",
    "eslint": "latest",
    "eslint-plugin-react-hooks": "latest",
    "eslint-plugin-react-refresh": "latest",
    "jsdom": "latest",
    "postcss": "latest",
    "tailwindcss": "latest",
    "typescript": "latest",
    "typescript-eslint": "latest",
    "vite": "latest",
    "vitest": "latest"
  }
}
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>QA RAG</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "files": [],
  "references": [{ "path": "./tsconfig.node.json" }],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "strict": true,
    "noEmit": true
  },
  "include": ["vite.config.ts", "eslint.config.js"]
}
```

Create `frontend/vite.config.ts`:

```ts
import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
  },
})
```

Create `frontend/eslint.config.js`:

```js
import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: { document: 'readonly', window: 'readonly', localStorage: 'readonly' },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
)
```

Create `frontend/src/test/setup.ts`:

```ts
import '@testing-library/jest-dom/vitest'
```

Create `frontend/src/App.tsx`:

```tsx
export default function App() {
  return <div className="min-h-screen bg-background text-foreground">QA RAG</div>
}
```

Create `frontend/src/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

Create `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222 47% 6%;
    --foreground: 210 40% 98%;
    --card: 222 47% 9%;
    --card-foreground: 210 40% 98%;
    --popover: 222 47% 9%;
    --popover-foreground: 210 40% 98%;
    --primary: 189 94% 43%;
    --primary-foreground: 222 47% 6%;
    --secondary: 217 33% 17%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217 33% 17%;
    --muted-foreground: 215 20% 65%;
    --accent: 262 83% 66%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 210 40% 98%;
    --border: 217 33% 17%;
    --input: 217 33% 17%;
    --ring: 189 94% 43%;
    --radius: 0.75rem;
  }

  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground antialiased;
  }
}
```

- [ ] **Step 2: Install dependencies**

Run:

```bash
cd frontend && npm install
```

Expected: `package-lock.json` created and install exits 0.

- [ ] **Step 3: Verify scaffold fails only for missing Tailwind config**

Run:

```bash
cd frontend && npm run build
```

Expected: build may fail because Tailwind/PostCSS config not yet created. If it passes, continue.

- [ ] **Step 4: Commit scaffold**

```bash
git add frontend
git commit -m "feat: scaffold frontend app"
```

---

### Task 2: Add Tailwind and shadcn base

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`
- Create/Modify via CLI: `frontend/src/components/ui/*`

- [ ] **Step 1: Create Tailwind/shadcn config**

Create `frontend/tailwind.config.ts`:

```ts
import type { Config } from 'tailwindcss'

const config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config

export default config
```

Create `frontend/postcss.config.js`:

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Create `frontend/components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

Create `frontend/src/lib/utils.ts`:

```ts
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: Install exactly approved shadcn modules**

Run:

```bash
cd frontend && npx shadcn@latest add button input textarea dialog toast skeleton badge scroll-area separator avatar card label progress
```

Expected: files generated under `frontend/src/components/ui`. Do not add other shadcn modules.

- [ ] **Step 3: Verify build**

Run:

```bash
cd frontend && npm run build
```

Expected: `built in` message and `dist/` created.

- [ ] **Step 4: Commit Tailwind/shadcn base**

```bash
git add frontend
git commit -m "feat: add tailwind and shadcn base"
```

---

### Task 3: Add domain types and fake adapters

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/services/authService.ts`
- Create: `frontend/src/services/documentService.ts`
- Create: `frontend/src/services/chatService.ts`

- [ ] **Step 1: Create shared types**

Create `frontend/src/types/index.ts`:

```ts
export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed'
export type MessageRole = 'user' | 'assistant'
export type MessageStatus = 'sent' | 'loading' | 'failed'

export interface User {
  id: string
  name: string
  email: string
}

export interface RagDocument {
  id: string
  name: string
  type: string
  sizeLabel: string
  uploadedAt: string
  status: DocumentStatus
  progress: number
  summary: string
  errorMessage?: string
}

export interface Citation {
  id: string
  documentId: string
  documentName: string
  page: number
  snippet: string
}

export interface ChatError {
  message: string
  retryable: boolean
  originalQuery?: string
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  status: MessageStatus
  createdAt: string
  error?: ChatError
  citations?: Citation[]
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

export interface SimulationSettings {
  failNextChat: boolean
  failNextUpload: boolean
}
```

- [ ] **Step 2: Create fake service adapters**

Create `frontend/src/services/authService.ts`:

```ts
import type { User } from '@/types'

const demoUser: User = {
  id: 'user-demo',
  name: 'RAG Reviewer',
  email: 'reviewer@example.com',
}

export async function login(email: string, _password: string): Promise<{ token: string; user: User }> {
  await delay(250)
  return { token: `fake-token-${email}`, user: { ...demoUser, email } }
}

export async function register(name: string, email: string, _password: string): Promise<{ token: string; user: User }> {
  await delay(300)
  return { token: `fake-token-${email}`, user: { ...demoUser, name, email } }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
```

Create `frontend/src/services/documentService.ts`:

```ts
import type { RagDocument } from '@/types'

export const seededDocuments: RagDocument[] = [
  {
    id: 'doc-architecture',
    name: 'System Architecture Brief.pdf',
    type: 'PDF',
    sizeLabel: '1.8 MB',
    uploadedAt: 'Today, 9:12 AM',
    status: 'ready',
    progress: 100,
    summary: 'Architecture notes covering ingestion, chunking, retrieval, and answer generation.',
  },
  {
    id: 'doc-policy',
    name: 'Security Policy Draft.docx',
    type: 'DOCX',
    sizeLabel: '860 KB',
    uploadedAt: 'Today, 9:18 AM',
    status: 'processing',
    progress: 64,
    summary: 'Policy draft currently moving through chunking and embedding.',
  },
  {
    id: 'doc-failed',
    name: 'Legacy Export.txt',
    type: 'TXT',
    sizeLabel: '420 KB',
    uploadedAt: 'Yesterday, 4:03 PM',
    status: 'failed',
    progress: 22,
    summary: 'Import failed before embedding completed.',
    errorMessage: 'Document parser could not detect a valid text encoding.',
  },
]

export async function createUploadingDocument(file: File): Promise<RagDocument> {
  await delay(350)
  return {
    id: `doc-${Date.now()}`,
    name: file.name,
    type: file.name.split('.').pop()?.toUpperCase() ?? 'FILE',
    sizeLabel: formatBytes(file.size),
    uploadedAt: 'Just now',
    status: 'uploading',
    progress: 20,
    summary: 'Upload accepted. Preparing document for processing.',
  }
}

export async function processDocument(document: RagDocument, shouldFail: boolean): Promise<RagDocument> {
  await delay(650)
  if (shouldFail) {
    return {
      ...document,
      status: 'failed',
      progress: 35,
      summary: 'Processing failed before embeddings were created.',
      errorMessage: 'Simulated upload failure: worker could not complete processing.',
    }
  }

  await delay(850)
  return {
    ...document,
    status: 'ready',
    progress: 100,
    summary: 'Document indexed and ready for question answering.',
    errorMessage: undefined,
  }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
```

Create `frontend/src/services/chatService.ts`:

```ts
import type { ChatResponse, RagDocument } from '@/types'

export async function askQuestion(document: RagDocument, query: string, shouldFail: boolean): Promise<ChatResponse> {
  await delay(900)

  if (shouldFail) {
    throw new Error('Simulated chat error: retrieval worker timed out before returning an answer.')
  }

  return {
    answer: `Based on ${document.name}, the most relevant answer is that the QA RAG pipeline should keep ingestion, retrieval, and answer generation observable through clear status states. Your question was: “${query}”.`,
    citations: [
      {
        id: `citation-${Date.now()}-1`,
        documentId: document.id,
        documentName: document.name,
        page: 2,
        snippet: 'The ingestion pipeline should expose progress from upload through embedding completion.',
      },
      {
        id: `citation-${Date.now()}-2`,
        documentId: document.id,
        documentName: document.name,
        page: 5,
        snippet: 'Answer generation should return citations with enough context for reviewers to trust the result.',
      },
    ],
  }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
```

- [ ] **Step 3: Verify no component file contains fake timers**

Run:

```bash
cd frontend && grep -R "setTimeout\|seededDocuments\|Simulated" src/components src/pages || true
```

Expected: no output.

- [ ] **Step 4: Build**

Run:

```bash
cd frontend && npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit types and adapters**

```bash
git add frontend/src/types frontend/src/services
git commit -m "feat: add frontend domain adapters"
```

---

### Task 4: Add Session and routing

**Files:**
- Create: `frontend/src/store/SessionContext.tsx`
- Create: `frontend/src/components/layout/AuthGuard.tsx`
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/pages/Register.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/store/__tests__/SessionContext.test.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write tests**

Create `frontend/src/store/__tests__/SessionContext.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { SessionProvider, useSession } from '../SessionContext'

function Probe() {
  const session = useSession()
  return (
    <div>
      <div>status:{session.isAuthenticated ? 'authed' : 'guest'}</div>
      <div>redirect:{session.getDefaultRedirect()}</div>
      <button onClick={() => void session.login('agent@example.com', 'password')}>login</button>
    </div>
  )
}

describe('Session module', () => {
  it('centralizes guest and authenticated redirects', async () => {
    render(
      <SessionProvider>
        <Probe />
      </SessionProvider>,
    )

    expect(screen.getByText('status:guest')).toBeInTheDocument()
    expect(screen.getByText('redirect:/login')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'login' }))

    expect(await screen.findByText('status:authed')).toBeInTheDocument()
    expect(screen.getByText('redirect:/chat')).toBeInTheDocument()
  })
})
```

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App routing', () => {
  it('redirects unauthenticated users to login', async () => {
    window.history.pushState({}, '', '/chat')
    render(<App />)
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
cd frontend && npm run test -- SessionContext App
```

Expected: FAIL because SessionContext/routes do not exist.

- [ ] **Step 3: Implement Session and routes**

Create `frontend/src/store/SessionContext.tsx`:

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import * as authService from '@/services/authService'
import type { User } from '@/types'

interface SessionContextValue {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  getDefaultRedirect: () => '/chat' | '/login'
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)

  const value = useMemo<SessionContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(token),
    async login(email, password) {
      const result = await authService.login(email, password)
      setToken(result.token)
      setUser(result.user)
    },
    async register(name, email, password) {
      const result = await authService.register(name, email, password)
      setToken(result.token)
      setUser(result.user)
    },
    logout() {
      setToken(null)
      setUser(null)
    },
    getDefaultRedirect() {
      return token ? '/chat' : '/login'
    },
  }), [token, user])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession must be used within SessionProvider')
  return value
}
```

Create `frontend/src/components/layout/AuthGuard.tsx`:

```tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useSession } from '@/store/SessionContext'

export function AuthGuard() {
  const session = useSession()
  const location = useLocation()

  if (!session.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
```

Create `frontend/src/pages/Login.tsx`:

```tsx
import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSession } from '@/store/SessionContext'

export default function Login() {
  const session = useSession()
  const navigate = useNavigate()
  const [email, setEmail] = useState('reviewer@example.com')
  const [password, setPassword] = useState('password')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setIsSubmitting(true)
    await session.login(email, password)
    navigate('/chat', { replace: true })
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md border-border/80 bg-card/80 shadow-2xl shadow-cyan-950/30">
        <CardHeader>
          <CardTitle className="text-2xl">Welcome back</CardTitle>
          <CardDescription>Sign in with the fake reviewer account to open the QA RAG workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <Button className="w-full" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'}</Button>
          </form>
          <p className="mt-4 text-sm text-muted-foreground">Need an account? <Link className="text-primary" to="/register">Register</Link></p>
        </CardContent>
      </Card>
    </main>
  )
}
```

Create `frontend/src/pages/Register.tsx`:

```tsx
import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSession } from '@/store/SessionContext'

export default function Register() {
  const session = useSession()
  const navigate = useNavigate()
  const [name, setName] = useState('RAG Reviewer')
  const [email, setEmail] = useState('reviewer@example.com')
  const [password, setPassword] = useState('password')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setIsSubmitting(true)
    await session.register(name, email, password)
    navigate('/chat', { replace: true })
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md border-border/80 bg-card/80 shadow-2xl shadow-violet-950/30">
        <CardHeader>
          <CardTitle className="text-2xl">Create account</CardTitle>
          <CardDescription>Register a fake account and continue to the QA RAG workspace.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2"><Label htmlFor="name">Name</Label><Input id="name" value={name} onChange={(event) => setName(event.target.value)} /></div>
            <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" value={email} onChange={(event) => setEmail(event.target.value)} /></div>
            <div className="space-y-2"><Label htmlFor="password">Password</Label><Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></div>
            <Button className="w-full" disabled={isSubmitting}>{isSubmitting ? 'Creating…' : 'Create account'}</Button>
          </form>
          <p className="mt-4 text-sm text-muted-foreground">Already registered? <Link className="text-primary" to="/login">Sign in</Link></p>
        </CardContent>
      </Card>
    </main>
  )
}
```

Modify `frontend/src/App.tsx`:

```tsx
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { useSession, SessionProvider } from '@/store/SessionContext'
import Login from '@/pages/Login'
import Register from '@/pages/Register'

function RootRedirect() {
  const session = useSession()
  return <Navigate to={session.getDefaultRedirect()} replace />
}

function ChatPlaceholder() {
  return <div className="min-h-screen bg-background p-8 text-foreground">Chat workspace</div>
}

const router = createBrowserRouter([
  { path: '/', element: <RootRedirect /> },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    element: <AuthGuard />,
    children: [{ path: '/chat', element: <ChatPlaceholder /> }],
  },
  { path: '*', element: <RootRedirect /> },
])

export default function App() {
  return (
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  )
}
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd frontend && npm run test -- SessionContext App
```

Expected: PASS.

- [ ] **Step 5: Commit Session Module**

```bash
git add frontend/src
git commit -m "feat: add session routing"
```

---

### Task 5: Add Simulation Profile and Document Pipeline

**Files:**
- Create: `frontend/src/store/SimulationProfileContext.tsx`
- Create: `frontend/src/store/DocumentPipelineContext.tsx`
- Test: `frontend/src/store/__tests__/DocumentPipelineContext.test.tsx`

- [ ] **Step 1: Write Document Pipeline test**

Create `frontend/src/store/__tests__/DocumentPipelineContext.test.tsx`:

```tsx
import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DocumentPipelineProvider, useDocumentPipeline } from '../DocumentPipelineContext'
import { SimulationProfileProvider, useSimulationProfile } from '../SimulationProfileContext'

function wrapper({ children }: { children: React.ReactNode }) {
  return <SimulationProfileProvider><DocumentPipelineProvider>{children}</DocumentPipelineProvider></SimulationProfileProvider>
}

describe('Document Pipeline module', () => {
  it('uploads a document through ready status', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), { wrapper })
    const file = new File(['hello'], 'review-notes.pdf', { type: 'application/pdf' })

    await act(async () => { await result.current.upload(file) })

    expect(result.current.documents.some((doc) => doc.name === 'review-notes.pdf')).toBe(true)
    await waitFor(() => expect(result.current.documents.find((doc) => doc.name === 'review-notes.pdf')?.status).toBe('ready'), { timeout: 3000 })
  })

  it('fails deterministically and retries through ready status', async () => {
    const { result } = renderHook(() => ({ pipeline: useDocumentPipeline(), simulation: useSimulationProfile() }), { wrapper })
    const file = new File(['hello'], 'failure-case.pdf', { type: 'application/pdf' })

    act(() => result.current.simulation.setFailNextUpload(true))
    await act(async () => { await result.current.pipeline.upload(file) })

    await waitFor(() => expect(result.current.pipeline.documents.find((doc) => doc.name === 'failure-case.pdf')?.status).toBe('failed'), { timeout: 3000 })
    const failed = result.current.pipeline.documents.find((doc) => doc.name === 'failure-case.pdf')!

    await act(async () => { await result.current.pipeline.retry(failed.id) })

    await waitFor(() => expect(result.current.pipeline.documents.find((doc) => doc.id === failed.id)?.status).toBe('ready'), { timeout: 3000 })
  })
})
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
cd frontend && npm run test -- DocumentPipelineContext
```

Expected: FAIL because contexts do not exist.

- [ ] **Step 3: Implement Simulation Profile and Document Pipeline**

Create `frontend/src/store/SimulationProfileContext.tsx`:

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

interface SimulationProfileValue {
  failNextChat: boolean
  failNextUpload: boolean
  setFailNextChat: (value: boolean) => void
  setFailNextUpload: (value: boolean) => void
  consumeUploadFailure: () => boolean
  consumeChatFailure: () => boolean
}

const SimulationProfileContext = createContext<SimulationProfileValue | null>(null)

export function SimulationProfileProvider({ children }: { children: ReactNode }) {
  const [failNextChat, setFailNextChat] = useState(false)
  const [failNextUpload, setFailNextUpload] = useState(false)

  const value = useMemo<SimulationProfileValue>(() => ({
    failNextChat,
    failNextUpload,
    setFailNextChat,
    setFailNextUpload,
    consumeUploadFailure() {
      if (!failNextUpload) return false
      setFailNextUpload(false)
      return true
    },
    consumeChatFailure() {
      if (!failNextChat) return false
      setFailNextChat(false)
      return true
    },
  }), [failNextChat, failNextUpload])

  return <SimulationProfileContext.Provider value={value}>{children}</SimulationProfileContext.Provider>
}

export function useSimulationProfile() {
  const value = useContext(SimulationProfileContext)
  if (!value) throw new Error('useSimulationProfile must be used within SimulationProfileProvider')
  return value
}
```

Create `frontend/src/store/DocumentPipelineContext.tsx`:

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { createUploadingDocument, processDocument, seededDocuments } from '@/services/documentService'
import type { RagDocument } from '@/types'
import { useSimulationProfile } from './SimulationProfileContext'

interface DocumentPipelineValue {
  documents: RagDocument[]
  activeDocument: RagDocument | null
  upload: (file: File) => Promise<void>
  retry: (documentId: string) => Promise<void>
  selectDocument: (documentId: string) => void
}

const DocumentPipelineContext = createContext<DocumentPipelineValue | null>(null)

export function DocumentPipelineProvider({ children }: { children: ReactNode }) {
  const simulation = useSimulationProfile()
  const [documents, setDocuments] = useState<RagDocument[]>(seededDocuments)
  const [activeDocumentId, setActiveDocumentId] = useState('doc-architecture')

  async function upload(file: File) {
    const uploading = await createUploadingDocument(file)
    setDocuments((current) => [uploading, ...current])
    const shouldFail = simulation.consumeUploadFailure()
    const processed = await processDocument(uploading, shouldFail)
    setDocuments((current) => current.map((doc) => doc.id === processed.id ? processed : doc))
    if (processed.status === 'ready') setActiveDocumentId(processed.id)
  }

  async function retry(documentId: string) {
    const current = documents.find((doc) => doc.id === documentId)
    if (!current) return
    const uploading: RagDocument = { ...current, status: 'uploading', progress: 20, errorMessage: undefined, summary: 'Retry accepted. Uploading document again.' }
    setDocuments((docs) => docs.map((doc) => doc.id === documentId ? uploading : doc))
    const processed = await processDocument(uploading, false)
    setDocuments((docs) => docs.map((doc) => doc.id === documentId ? processed : doc))
    setActiveDocumentId(processed.id)
  }

  function selectDocument(documentId: string) {
    const selected = documents.find((doc) => doc.id === documentId)
    if (selected?.status === 'ready') setActiveDocumentId(documentId)
  }

  const activeDocument = documents.find((doc) => doc.id === activeDocumentId && doc.status === 'ready') ?? null

  const value = useMemo(() => ({ documents, activeDocument, upload, retry, selectDocument }), [documents, activeDocument])

  return <DocumentPipelineContext.Provider value={value}>{children}</DocumentPipelineContext.Provider>
}

export function useDocumentPipeline() {
  const value = useContext(DocumentPipelineContext)
  if (!value) throw new Error('useDocumentPipeline must be used within DocumentPipelineProvider')
  return value
}
```

- [ ] **Step 4: Run test**

Run:

```bash
cd frontend && npm run test -- DocumentPipelineContext
```

Expected: PASS.

- [ ] **Step 5: Commit Document Pipeline**

```bash
git add frontend/src/store frontend/src/store/__tests__
git commit -m "feat: add document pipeline module"
```

---

### Task 6: Add Conversation Module

**Files:**
- Create: `frontend/src/store/ConversationContext.tsx`
- Test: `frontend/src/store/__tests__/ConversationContext.test.tsx`

- [ ] **Step 1: Write Conversation tests**

Create `frontend/src/store/__tests__/ConversationContext.test.tsx`:

```tsx
import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ConversationProvider, useConversation } from '../ConversationContext'
import { DocumentPipelineProvider } from '../DocumentPipelineContext'
import { SimulationProfileProvider, useSimulationProfile } from '../SimulationProfileContext'

function wrapper({ children }: { children: React.ReactNode }) {
  return <SimulationProfileProvider><DocumentPipelineProvider><ConversationProvider>{children}</ConversationProvider></DocumentPipelineProvider></SimulationProfileProvider>
}

describe('Conversation module', () => {
  it('answers with citations for the active ready document', async () => {
    const { result } = renderHook(() => useConversation(), { wrapper })

    await act(async () => { await result.current.send('How does processing work?') })

    await waitFor(() => expect(result.current.messages.some((message) => message.role === 'assistant' && message.status === 'sent')).toBe(true), { timeout: 3000 })
    expect(result.current.latestCitations).toHaveLength(2)
  })

  it('stores failed assistant message and retries original query', async () => {
    const { result } = renderHook(() => ({ conversation: useConversation(), simulation: useSimulationProfile() }), { wrapper })

    act(() => result.current.simulation.setFailNextChat(true))
    await act(async () => { await result.current.conversation.send('Trigger failure') })

    await waitFor(() => expect(result.current.conversation.messages.some((message) => message.status === 'failed')).toBe(true), { timeout: 3000 })
    const failed = result.current.conversation.messages.find((message) => message.status === 'failed')!
    expect(failed.error?.originalQuery).toBe('Trigger failure')

    await act(async () => { await result.current.conversation.retry(failed.id) })

    await waitFor(() => expect(result.current.conversation.messages.some((message) => message.role === 'assistant' && message.status === 'sent')).toBe(true), { timeout: 3000 })
  })
})
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
cd frontend && npm run test -- ConversationContext
```

Expected: FAIL because ConversationContext does not exist.

- [ ] **Step 3: Implement ConversationContext**

Create `frontend/src/store/ConversationContext.tsx`:

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { askQuestion } from '@/services/chatService'
import type { Citation, Message } from '@/types'
import { useDocumentPipeline } from './DocumentPipelineContext'
import { useSimulationProfile } from './SimulationProfileContext'

interface ConversationValue {
  messages: Message[]
  latestCitations: Citation[]
  isSending: boolean
  send: (query: string) => Promise<void>
  retry: (messageId: string) => Promise<void>
}

const ConversationContext = createContext<ConversationValue | null>(null)

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { activeDocument } = useDocumentPipeline()
  const simulation = useSimulationProfile()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'assistant-welcome',
      role: 'assistant',
      content: 'Select a ready document and ask a question. I will return a grounded answer with citations.',
      status: 'sent',
      createdAt: 'Just now',
    },
  ])
  const [latestCitations, setLatestCitations] = useState<Citation[]>([])
  const [isSending, setIsSending] = useState(false)

  async function send(query: string) {
    if (!activeDocument || !query.trim()) return
    const originalQuery = query.trim()
    const loadingId = `assistant-${Date.now()}`
    setIsSending(true)
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: 'user', content: originalQuery, status: 'sent', createdAt: 'Just now' },
      { id: loadingId, role: 'assistant', content: 'Searching sources and drafting answer…', status: 'loading', createdAt: 'Just now' },
    ])

    try {
      const response = await askQuestion(activeDocument, originalQuery, simulation.consumeChatFailure())
      setLatestCitations(response.citations)
      setMessages((current) => current.map((message) => message.id === loadingId ? {
        ...message,
        content: response.answer,
        status: 'sent',
        citations: response.citations,
      } : message))
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The assistant could not answer this question.'
      setMessages((current) => current.map((item) => item.id === loadingId ? {
        ...item,
        content: message,
        status: 'failed',
        error: { message, retryable: true, originalQuery },
      } : item))
    } finally {
      setIsSending(false)
    }
  }

  async function retry(messageId: string) {
    const failed = messages.find((message) => message.id === messageId)
    const originalQuery = failed?.error?.originalQuery
    if (!originalQuery) return
    setMessages((current) => current.filter((message) => message.id !== messageId))
    await send(originalQuery)
  }

  const value = useMemo(() => ({ messages, latestCitations, isSending, send, retry }), [messages, latestCitations, isSending, activeDocument])

  return <ConversationContext.Provider value={value}>{children}</ConversationContext.Provider>
}

export function useConversation() {
  const value = useContext(ConversationContext)
  if (!value) throw new Error('useConversation must be used within ConversationProvider')
  return value
}
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd frontend && npm run test -- ConversationContext
```

Expected: PASS.

- [ ] **Step 5: Commit Conversation Module**

```bash
git add frontend/src/store
git commit -m "feat: add conversation module"
```

---

### Task 7: Build chat workspace UI

**Files:**
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/TopBar.tsx`
- Create: `frontend/src/components/layout/SimulationControls.tsx`
- Create: `frontend/src/components/documents/UploadPanel.tsx`
- Create: `frontend/src/components/documents/DocumentList.tsx`
- Create: `frontend/src/components/documents/DocumentCard.tsx`
- Create: `frontend/src/components/chat/ChatThread.tsx`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/ChatInput.tsx`
- Create: `frontend/src/components/chat/CitationCard.tsx`
- Create: `frontend/src/components/chat/CitationPanel.tsx`
- Create: `frontend/src/pages/Chat.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Implement layout and document UI**

Create `frontend/src/components/layout/TopBar.tsx`:

```tsx
import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useSession } from '@/store/SessionContext'

export function TopBar() {
  const session = useSession()
  return (
    <header className="flex items-center justify-between border-b border-border/70 bg-card/50 px-6 py-4 backdrop-blur">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">QA RAG Workspace</h1>
        <p className="text-sm text-muted-foreground">Ask grounded questions over selected documents.</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden text-sm text-muted-foreground sm:inline">{session.user?.email}</span>
        <Separator orientation="vertical" className="h-6" />
        <Button variant="ghost" size="sm" onClick={session.logout}><LogOut className="mr-2 size-4" />Logout</Button>
      </div>
    </header>
  )
}
```

Create `frontend/src/components/layout/SimulationControls.tsx`:

```tsx
import { Label } from '@/components/ui/label'
import { useSimulationProfile } from '@/store/SimulationProfileContext'

export function SimulationControls() {
  const simulation = useSimulationProfile()
  return (
    <section className="rounded-lg border border-dashed border-border/80 bg-muted/30 p-3 text-xs text-muted-foreground">
      <p className="mb-2 font-medium text-foreground">Simulation controls</p>
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-4">
        <Label className="flex items-center gap-2"><input type="checkbox" checked={simulation.failNextChat} onChange={(event) => simulation.setFailNextChat(event.target.checked)} />Simulate chat error</Label>
        <Label className="flex items-center gap-2"><input type="checkbox" checked={simulation.failNextUpload} onChange={(event) => simulation.setFailNextUpload(event.target.checked)} />Simulate upload failure</Label>
      </div>
    </section>
  )
}
```

Create `frontend/src/components/documents/DocumentCard.tsx`:

```tsx
import { AlertCircle, CheckCircle2, Clock3, UploadCloud } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import type { RagDocument } from '@/types'

interface DocumentCardProps {
  document: RagDocument
  isActive: boolean
  onSelect: () => void
  onRetry: () => void
}

export function DocumentCard({ document, isActive, onSelect, onRetry }: DocumentCardProps) {
  const icon = document.status === 'ready' ? <CheckCircle2 className="size-4 text-emerald-400" /> : document.status === 'failed' ? <AlertCircle className="size-4 text-destructive" /> : document.status === 'uploading' ? <UploadCloud className="size-4 text-primary" /> : <Clock3 className="size-4 text-accent" />
  return (
    <Card className={cn('cursor-pointer border-border/70 bg-card/70 transition hover:border-primary/60', isActive && 'border-primary/80 shadow-lg shadow-cyan-950/30')} onClick={document.status === 'ready' ? onSelect : undefined}>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0"><p className="truncate font-medium">{document.name}</p><p className="text-xs text-muted-foreground">{document.type} · {document.sizeLabel} · {document.uploadedAt}</p></div>
          <Badge variant={document.status === 'failed' ? 'destructive' : 'secondary'} className="gap-1">{icon}{document.status}</Badge>
        </div>
        <Progress value={document.progress} />
        <p className="text-xs text-muted-foreground">{document.errorMessage ?? document.summary}</p>
        {document.status === 'failed' && <Button size="sm" variant="secondary" onClick={(event) => { event.stopPropagation(); onRetry() }}>Retry</Button>}
      </CardContent>
    </Card>
  )
}
```

Create `frontend/src/components/documents/DocumentList.tsx`:

```tsx
import { ScrollArea } from '@/components/ui/scroll-area'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'
import { DocumentCard } from './DocumentCard'

export function DocumentList() {
  const pipeline = useDocumentPipeline()
  return (
    <ScrollArea className="h-[420px] pr-3">
      <div className="space-y-3">
        {pipeline.documents.map((document) => (
          <DocumentCard key={document.id} document={document} isActive={pipeline.activeDocument?.id === document.id} onSelect={() => pipeline.selectDocument(document.id)} onRetry={() => void pipeline.retry(document.id)} />
        ))}
      </div>
    </ScrollArea>
  )
}
```

Create `frontend/src/components/documents/UploadPanel.tsx`:

```tsx
import { useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function UploadPanel() {
  const pipeline = useDocumentPipeline()
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  async function upload() {
    if (!file) return
    setIsUploading(true)
    await pipeline.upload(file)
    setFile(null)
    setIsUploading(false)
  }

  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UploadCloud className="size-4 text-primary" />Upload document</CardTitle><CardDescription>Fake upload pipeline with processing states.</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Label htmlFor="document-upload">Document file</Label>
        <Input id="document-upload" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <Button className="w-full" disabled={!file || isUploading} onClick={() => void upload()}>{isUploading ? 'Uploading…' : 'Upload'}</Button>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 2: Implement chat UI**

Create `frontend/src/components/chat/MessageBubble.tsx`:

```tsx
import { Bot, RefreshCw, User } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

export function MessageBubble({ message, onRetry }: { message: Message; onRetry: () => void }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-3', isUser && 'justify-end')}>
      {!isUser && <Avatar><AvatarFallback><Bot className="size-4" /></AvatarFallback></Avatar>}
      <div className={cn('max-w-[80%] rounded-2xl border px-4 py-3 text-sm', isUser ? 'border-primary/50 bg-primary text-primary-foreground' : 'border-border bg-card')}>
        {message.status === 'loading' ? <div className="space-y-2"><Skeleton className="h-4 w-56" /><Skeleton className="h-4 w-40" /></div> : <p>{message.content}</p>}
        {message.status === 'failed' && message.error?.retryable && <Button className="mt-3" size="sm" variant="secondary" onClick={onRetry}><RefreshCw className="mr-2 size-4" />Retry</Button>}
      </div>
      {isUser && <Avatar><AvatarFallback><User className="size-4" /></AvatarFallback></Avatar>}
    </div>
  )
}
```

Create `frontend/src/components/chat/ChatThread.tsx`:

```tsx
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { MessageBubble } from './MessageBubble'

export function ChatThread() {
  const conversation = useConversation()
  return (
    <ScrollArea className="h-[58vh] pr-4">
      <div className="space-y-5">
        {conversation.messages.map((message) => <MessageBubble key={message.id} message={message} onRetry={() => void conversation.retry(message.id)} />)}
      </div>
    </ScrollArea>
  )
}
```

Create `frontend/src/components/chat/ChatInput.tsx`:

```tsx
import { FormEvent, useState } from 'react'
import { SendHorizonal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useConversation } from '@/store/ConversationContext'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function ChatInput() {
  const conversation = useConversation()
  const pipeline = useDocumentPipeline()
  const [query, setQuery] = useState('What does this document say about the RAG pipeline?')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const value = query.trim()
    if (!value) return
    setQuery('')
    await conversation.send(value)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <Textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder={pipeline.activeDocument ? 'Ask a question about the selected document…' : 'Select a ready document first…'} disabled={!pipeline.activeDocument || conversation.isSending} />
      <Button type="submit" disabled={!pipeline.activeDocument || conversation.isSending || !query.trim()}><SendHorizonal className="mr-2 size-4" />Send</Button>
    </form>
  )
}
```

Create `frontend/src/components/chat/CitationCard.tsx`:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Citation } from '@/types'

export function CitationCard({ citation }: { citation: Citation }) {
  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader className="pb-2"><CardTitle className="text-sm">Source: page {citation.page}</CardTitle></CardHeader>
      <CardContent><p className="text-xs text-muted-foreground">{citation.documentName}</p><p className="mt-2 text-sm">{citation.snippet}</p></CardContent>
    </Card>
  )
}
```

Create `frontend/src/components/chat/CitationPanel.tsx`:

```tsx
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { CitationCard } from './CitationCard'

export function CitationPanel() {
  const conversation = useConversation()
  return (
    <aside className="space-y-3">
      <div><h2 className="font-semibold">Sources</h2><p className="text-sm text-muted-foreground">Latest answer citations.</p></div>
      <ScrollArea className="h-[70vh] pr-3">
        <div className="space-y-3">
          {conversation.latestCitations.length === 0 ? <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">Ask a question to populate citations.</p> : conversation.latestCitations.map((citation) => <CitationCard key={citation.id} citation={citation} />)}
        </div>
      </ScrollArea>
    </aside>
  )
}
```

- [ ] **Step 3: Compose Chat page and providers**

Create `frontend/src/components/layout/AppShell.tsx`:

```tsx
import { ReactNode } from 'react'
import { TopBar } from './TopBar'

export function AppShell({ left, center, right }: { left: ReactNode; center: ReactNode; right: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.18),transparent_32%),hsl(var(--background))] text-foreground">
      <TopBar />
      <main className="grid gap-5 p-5 lg:grid-cols-[320px_minmax(0,1fr)_320px]">
        <section className="space-y-4">{left}</section>
        <section className="rounded-2xl border border-border/70 bg-card/60 p-4 shadow-2xl shadow-cyan-950/20">{center}</section>
        <section className="rounded-2xl border border-border/70 bg-card/40 p-4">{right}</section>
      </main>
    </div>
  )
}
```

Create `frontend/src/pages/Chat.tsx`:

```tsx
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatThread } from '@/components/chat/ChatThread'
import { CitationPanel } from '@/components/chat/CitationPanel'
import { DocumentList } from '@/components/documents/DocumentList'
import { UploadPanel } from '@/components/documents/UploadPanel'
import { AppShell } from '@/components/layout/AppShell'
import { SimulationControls } from '@/components/layout/SimulationControls'
import { Separator } from '@/components/ui/separator'
import { ConversationProvider } from '@/store/ConversationContext'
import { DocumentPipelineProvider } from '@/store/DocumentPipelineContext'
import { SimulationProfileProvider } from '@/store/SimulationProfileContext'

export default function Chat() {
  return (
    <SimulationProfileProvider>
      <DocumentPipelineProvider>
        <ConversationProvider>
          <AppShell
            left={<><UploadPanel /><div><h2 className="mb-3 font-semibold">Documents</h2><DocumentList /></div></>}
            center={<div className="space-y-4"><ChatThread /><Separator /><ChatInput /><SimulationControls /></div>}
            right={<CitationPanel />}
          />
        </ConversationProvider>
      </DocumentPipelineProvider>
    </SimulationProfileProvider>
  )
}
```

Modify `frontend/src/App.tsx` to use `Chat` instead of placeholder:

```tsx
import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { AuthGuard } from '@/components/layout/AuthGuard'
import { useSession, SessionProvider } from '@/store/SessionContext'
import Chat from '@/pages/Chat'
import Login from '@/pages/Login'
import Register from '@/pages/Register'

function RootRedirect() {
  const session = useSession()
  return <Navigate to={session.getDefaultRedirect()} replace />
}

const router = createBrowserRouter([
  { path: '/', element: <RootRedirect /> },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    element: <AuthGuard />,
    children: [{ path: '/chat', element: <Chat /> }],
  },
  { path: '*', element: <RootRedirect /> },
])

export default function App() {
  return (
    <SessionProvider>
      <RouterProvider router={router} />
    </SessionProvider>
  )
}
```

- [ ] **Step 4: Verify no fake timers in UI**

Run:

```bash
cd frontend && grep -R "setTimeout\|seededDocuments\|Simulated" src/components src/pages || true
```

Expected: no output.

- [ ] **Step 5: Run tests and build**

Run:

```bash
cd frontend && npm run test && npm run build && npm run lint
```

Expected: PASS.

- [ ] **Step 6: Commit chat workspace UI**

```bash
git add frontend/src
git commit -m "feat: build rag chat workspace"
```

---

### Task 8: Add Docker, compose, README, Makefile

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`
- Create: `Makefile`
- Create: `.env.example`
- Create/Modify: `README.md`

- [ ] **Step 1: Add Docker files**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS serve
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    try_files $uri =404;
  }
}
```

Create `docker-compose.yml`:

```yaml
services:
  frontend:
    build:
      context: ./frontend
    ports:
      - "8080:80"
```

- [ ] **Step 2: Add DX files**

Create `Makefile`:

```makefile
.PHONY: dev build docker-up docker-down docker-logs lint clean

dev:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f frontend

lint:
	cd frontend && npm run lint

clean:
	rm -rf frontend/node_modules frontend/dist frontend/.env
```

Create `.env.example`:

```bash
# Future backend API URL. Current frontend uses fake local adapters.
VITE_API_BASE_URL=http://localhost:8000
```

Create `README.md`:

```md
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
```

- [ ] **Step 3: Verify Docker build**

Run:

```bash
docker compose build frontend
```

Expected: image builds successfully.

- [ ] **Step 4: Commit Docker and docs**

```bash
git add frontend/Dockerfile frontend/nginx.conf docker-compose.yml Makefile README.md .env.example
git commit -m "chore: add frontend docker and docs"
```

---

### Task 9: Final verification

**Files:**
- Modify if needed: files from previous tasks only.

- [ ] **Step 1: Run static checks**

Run:

```bash
cd frontend && npm run lint && npm run test && npm run build
```

Expected: all pass.

- [ ] **Step 2: Verify no fake behavior leaked into UI**

Run:

```bash
cd frontend && grep -R "setTimeout\|seededDocuments\|Simulated" src/components src/pages || true
```

Expected: no output.

- [ ] **Step 3: Verify Docker serving**

Run:

```bash
docker compose up --build
```

Expected: frontend starts and serves at `http://localhost:8080`.

In another terminal, run:

```bash
curl -I http://localhost:8080/chat
```

Expected: HTTP 200, not 404. This verifies Nginx `try_files` handles React Router refresh.

- [ ] **Step 4: Manual browser verification**

Verify:

- unauthenticated `/chat` redirects to `/login`
- login redirects to `/chat`
- register redirects to `/chat`
- seeded docs appear populated
- upload success reaches Ready
- `Simulate upload failure` shows Failed and Retry reaches Ready
- chat success shows answer and citation cards
- `Simulate chat error` shows failed assistant message and Retry resends original query
- layout is 3-column on desktop and stacked on narrow screen

- [ ] **Step 5: Commit verification fixes if any**

If fixes were needed:

```bash
git add frontend docker-compose.yml Makefile README.md .env.example
git commit -m "fix: complete frontend verification"
```

If no fixes were needed, do not create an empty commit.

---

## Self-Review Notes

Spec coverage:

- React + TypeScript + Vite scaffold: Task 1.
- Tailwind + shadcn exact component set: Task 2.
- Deep modules and service seams: Tasks 3-6.
- Fake auth, redirects, guard: Task 4.
- Document Pipeline upload/processing/ready/failed/retry: Task 5 and Task 7.
- Chat loading/error/retry/citations: Task 6 and Task 7.
- 3-column desktop + stacked responsive UI: Task 7.
- Docker multi-stage + Nginx `try_files`: Task 8.
- Compose root service on `8080:80`: Task 8.
- README, Makefile, `.env.example`: Task 8.
- Verification checklist: Task 9.

Placeholder scan: no unresolved placeholder markers or undefined later-only names intentionally left.

Type consistency: plan uses `RagDocument` instead of `Document` to avoid collision with browser `Document`; `DocumentStatus`, `ChatError`, `Citation`, `Message`, and Module names remain aligned with the spec.
