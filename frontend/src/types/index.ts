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
