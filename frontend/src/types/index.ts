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
  label?: string
  chunkId?: string
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

export interface ConversationSummary {
  id: string
  activeDocumentIds: string[]
  needsRetry: boolean
  danglingUserMessageId?: string | null
}

export interface CitationSource {
  chunkId: string
  docId: string
  filename: string
  page: number | null
  snippet: string
}

export type ConversationStreamEvent =
  | { type: 'token'; value: string; reason?: string }
  | { type: 'citations'; map: Record<string, CitationSource> }
  | { type: 'error'; message: string; retryable: boolean }
  | { type: 'done' }

export interface SimulationSettings {
  failNextChat: boolean
  failNextUpload: boolean
}
