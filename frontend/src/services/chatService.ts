import { apiRequest } from './apiClient'
import type { ChatResponse, Citation, RagDocument } from '@/types'

interface ConversationOut {
  id: string
  document_id: string
  created_at: string
}

interface CitationOut {
  id: string
  document_id: string
  chunk_text: string
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

export async function createConversation(documentId: string): Promise<string> {
  const response = await apiRequest<ConversationOut>('/conversations', {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId }),
  })
  return response.id
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

function mapCitation(document: RagDocument): (c: CitationOut) => Citation {
  return (c: CitationOut) => ({
    id: c.id,
    documentId: c.document_id,
    documentName: document.name,
    page: c.page_number ?? 1,
    snippet: c.chunk_text,
  })
}
