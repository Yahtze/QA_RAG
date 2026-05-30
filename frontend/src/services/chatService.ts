import { apiRequest } from './apiClient'
import type { ChatResponse, Citation, ConversationSummary, Message, RagDocument } from '@/types'

interface ConversationOut {
  id: string
  document_id: string | null
  active_document_ids: string[]
  needs_retry: boolean
  dangling_user_message_id: string | null
  created_at: string
}

interface CitationOut {
  id: string
  document_id: string
  chunk_id?: string | null
  label?: string | null
  filename?: string | null
  chunk_text: string
  snippet?: string | null
  page_number: number | null
  score: number
}

interface MessageOut {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  citations: CitationOut[]
}

interface MessagePairOut {
  user_message: MessageOut
  assistant_message: MessageOut
}

interface CursorPage<T> {
  items: T[]
  page_info: { next_cursor: string | null; has_more: boolean }
}

export async function createConversation(
  documentId: string,
  activeDocumentIds?: string[],
): Promise<string> {
  const ids = activeDocumentIds && activeDocumentIds.length > 0 ? activeDocumentIds : [documentId]
  const response = await apiRequest<ConversationOut>('/conversations', {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      active_document_ids: ids,
    }),
  })
  return response.id
}

export async function updateActiveDocuments(
  conversationId: string,
  activeDocumentIds: string[],
): Promise<ConversationSummary> {
  const response = await apiRequest<ConversationOut>(
    `/conversations/${conversationId}/active-documents`,
    {
      method: 'PUT',
      body: JSON.stringify({ active_document_ids: activeDocumentIds }),
    },
  )
  return {
    id: response.id,
    activeDocumentIds: response.active_document_ids,
    needsRetry: response.needs_retry,
    danglingUserMessageId: response.dangling_user_message_id,
  }
}

export async function askQuestion(
  conversationId: string,
  document: RagDocument,
  query: string,
): Promise<ChatResponse> {
  const pair = await apiRequest<MessagePairOut>(
    `/conversations/${conversationId}/messages`,
    {
      method: 'POST',
      body: JSON.stringify({ content: query }),
    },
  )
  return {
    answer: pair.assistant_message.content,
    citations: pair.assistant_message.citations.map(mapCitation(document)),
  }
}

export async function listConversations(limit = 100): Promise<ConversationOut[]> {
  const page = await apiRequest<CursorPage<ConversationOut>>(`/conversations?limit=${limit}`)
  return page.items ?? []
}

export async function listMessages(conversationId: string, limit = 200): Promise<Message[]> {
  const page = await apiRequest<CursorPage<MessageOut>>(`/conversations/${conversationId}/messages?limit=${limit}`)
  return (page.items ?? []).map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    status: 'sent',
    createdAt: new Date(message.created_at).toLocaleString(),
    citations: message.citations.map((citation) => ({
      id: citation.id,
      label: citation.label ?? undefined,
      chunkId: citation.chunk_id ?? undefined,
      documentId: citation.document_id,
      documentName: citation.filename ?? 'Document',
      page: citation.page_number ?? 1,
      snippet: citation.snippet ?? citation.chunk_text,
    })),
  }))
}

function mapCitation(document: RagDocument): (c: CitationOut) => Citation {
  return (c: CitationOut) => ({
    id: c.id,
    label: c.label ?? undefined,
    chunkId: c.chunk_id ?? undefined,
    documentId: c.document_id,
    documentName: c.filename ?? document.name,
    page: c.page_number ?? 1,
    snippet: c.snippet ?? c.chunk_text,
  })
}
