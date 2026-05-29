import type { CitationSource, ConversationStreamEvent } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

function authHeaders(): HeadersInit {
  try {
    const token = globalThis.localStorage?.getItem('qa_rag_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  } catch {
    return {}
  }
}

async function apiError(response: Response): Promise<Error> {
  try {
    const payload = await response.json()
    return new Error(payload.detail ?? `Request failed with ${response.status}`)
  } catch {
    return new Error(`Request failed with ${response.status}`)
  }
}

type CitationWire = {
  chunkId?: string
  chunk_id?: string
  docId?: string
  doc_id?: string
  filename?: string
  page?: number | null
  snippet?: string
}

type StreamWire = {
  type?: string
  value?: unknown
  reason?: string
  message?: unknown
  retryable?: boolean
  map?: Record<string, CitationWire>
}

function normalizeEvent(raw: StreamWire): ConversationStreamEvent {
  if (raw?.type === 'citations') {
    const mapped = Object.fromEntries(
      Object.entries(raw.map ?? {}).map(([label, source]) => [
        label,
        {
          chunkId: source.chunkId ?? source.chunk_id ?? '',
          docId: source.docId ?? source.doc_id ?? '',
          filename: source.filename ?? '',
          page: source.page ?? null,
          snippet: source.snippet ?? '',
        } satisfies CitationSource,
      ]),
    )
    return { type: 'citations', map: mapped }
  }
  if (raw?.type === 'token') {
    return { type: 'token', value: String(raw.value ?? ''), reason: raw.reason }
  }
  if (raw?.type === 'error') {
    return {
      type: 'error',
      message: String(raw.message ?? 'The assistant could not answer this question.'),
      retryable: raw.retryable !== false,
    }
  }
  return { type: 'done' }
}

export async function* streamConversationMessage(
  conversationId: string,
  content: string,
): AsyncGenerator<ConversationStreamEvent> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...authHeaders(),
    },
    body: JSON.stringify({ content }),
  })

  if (!response.ok) {
    throw await apiError(response)
  }
  if (!response.body) {
    throw new Error('Streaming response body is missing')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const dataLine = frame
        .split('\n')
        .find((line) => line.startsWith('data: '))
      if (!dataLine) continue
      yield normalizeEvent(JSON.parse(dataLine.slice(6)))
    }
  }

  const tail = buffer.trim()
  if (tail.startsWith('data: ')) {
    yield normalizeEvent(JSON.parse(tail.slice(6)))
  }
}
