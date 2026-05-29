import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

import { createConversation as createConv } from '@/services/chatService'
import { streamConversationMessage } from '@/services/conversationStream'
import type { Citation, Message } from '@/types'

import { useDocumentPipeline } from './DocumentPipelineContext'

interface ConversationValue {
  conversationId: string | null
  messages: Message[]
  latestCitations: Citation[]
  isSending: boolean
  send: (query: string) => Promise<void>
  retry: (messageId: string) => Promise<void>
}

const ConversationContext = createContext<ConversationValue | null>(null)

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { activeDocument } = useDocumentPipeline()
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
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversationDocumentId, setConversationDocumentId] = useState<string | null>(null)

  async function ensureConversation(documentId: string): Promise<string> {
    if (conversationId && conversationDocumentId === documentId) {
      return conversationId
    }
    const id = await createConv(documentId)
    setConversationId(id)
    setConversationDocumentId(documentId)
    return id
  }

  async function send(query: string) {
    if (!activeDocument || !query.trim()) return
    const originalQuery = query.trim()
    const loadingId = `assistant-${Date.now()}`
    setIsSending(true)
    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: originalQuery,
        status: 'sent',
        createdAt: 'Just now',
      },
      {
        id: loadingId,
        role: 'assistant',
        content: 'Searching sources and drafting answer…',
        status: 'loading',
        createdAt: 'Just now',
      },
    ])

    try {
      const conversationId = await ensureConversation(activeDocument.id)
      for await (const event of streamConversationMessage(conversationId, originalQuery)) {
        if (event.type === 'token') {
          setMessages((current) =>
            current.map((message) =>
              message.id === loadingId
                ? {
                    ...message,
                    content:
                      (message.content === 'Searching sources and drafting answer…'
                        ? ''
                        : message.content) + event.value,
                    status: 'loading',
                  }
                : message,
            ),
          )
        } else if (event.type === 'citations') {
          const citations = Object.entries(event.map).map(([label, source]) => ({
            id: `${source.chunkId}-${label}`,
            label,
            chunkId: source.chunkId,
            documentId: source.docId,
            documentName: source.filename,
            page: source.page ?? 1,
            snippet: source.snippet,
          }))
          setLatestCitations(citations)
          setMessages((current) =>
            current.map((message) =>
              message.id === loadingId ? { ...message, citations } : message,
            ),
          )
        } else if (event.type === 'error') {
          setMessages((current) =>
            current.map((message) =>
              message.id === loadingId
                ? {
                    ...message,
                    content: event.message,
                    status: 'failed',
                    error: {
                      message: event.message,
                      retryable: event.retryable,
                      originalQuery,
                    },
                  }
                : message,
            ),
          )
        } else if (event.type === 'done') {
          setMessages((current) =>
            current.map((message) =>
              message.id === loadingId && message.status !== 'failed'
                ? { ...message, status: 'sent' }
                : message,
            ),
          )
        }
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'The assistant could not answer this question.'
      setMessages((current) =>
        current.map((item) =>
          item.id === loadingId
            ? {
                ...item,
                content: message,
                status: 'failed',
                error: { message, retryable: true, originalQuery },
              }
            : item,
        ),
      )
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

  const value = useMemo(
    () => ({
      conversationId,
      messages,
      latestCitations,
      isSending,
      send,
      retry,
    }),
    [conversationId, messages, latestCitations, isSending, activeDocument],
  )

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  )
}

export function useConversation() {
  const value = useContext(ConversationContext)
  if (!value) {
    throw new Error('useConversation must be used within ConversationProvider')
  }
  return value
}
