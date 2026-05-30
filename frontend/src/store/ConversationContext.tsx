import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { createConversation as createConv, listConversations, listMessages } from '@/services/chatService'
import { streamConversationMessage } from '@/services/conversationStream'
import type { Citation, Message } from '@/types'

import { useDocumentPipeline } from './DocumentPipelineContext'

interface ConversationValue {
  conversationId: string | null
  messages: Message[]
  latestCitations: Citation[]
  activeCitationId: string | null
  isSending: boolean
  send: (query: string) => Promise<void>
  retry: (messageId: string) => Promise<void>
  activateCitationByLabel: (label: string) => void
  newChat: () => void
}

function extractCitationLabels(content: string): Set<string> {
  const labels = new Set<string>()
  const pattern = /\[(\d+)]/g
  let match: RegExpExecArray | null = null
  while ((match = pattern.exec(content)) !== null) {
    if (match[1]) labels.add(match[1])
  }
  return labels
}

const ConversationContext = createContext<ConversationValue | null>(null)

function initialMessages(): Message[] {
  return [
    {
      id: 'assistant-welcome',
      role: 'assistant',
      content: 'Select a ready document and ask a question. I will return a grounded answer with citations.',
      status: 'sent',
      createdAt: 'Just now',
    },
  ]
}

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { activeDocument } = useDocumentPipeline()
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [latestCitations, setLatestCitations] = useState<Citation[]>([])
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null)
  const [isSending, setIsSending] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversationDocumentId, setConversationDocumentId] = useState<string | null>(null)
  const [isHydrating, setIsHydrating] = useState(false)

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
    if (!activeDocument || !query.trim() || isHydrating) return
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
          setMessages((current) => {
            const loadingMessage = current.find((message) => message.id === loadingId)
            const usedLabels = extractCitationLabels(loadingMessage?.content ?? '')
            const rawCitations = Object.entries(event.map)
              .filter(([label]) => usedLabels.size === 0 || usedLabels.has(label))
              .map(([label, source]) => ({
                id: `${source.chunkId}-${label}`,
                label,
                chunkId: source.chunkId,
                documentId: source.docId,
                documentName: source.filename,
                page: source.page ?? 1,
                snippet: source.snippet,
              }))

            const deduped = Array.from(
              new Map(rawCitations.map((citation) => [`${citation.chunkId}-${citation.label}`, citation])).values(),
            )

            setLatestCitations(deduped)
            setActiveCitationId(deduped[0]?.id ?? null)

            return current.map((message) =>
              message.id === loadingId ? { ...message, citations: deduped } : message,
            )
          })
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

  function activateCitationByLabel(label: string) {
    const match = latestCitations.find((citation) => citation.label === label)
    if (match) setActiveCitationId(match.id)
  }

  useEffect(() => {
    if (!activeDocument) return
    const activeDocumentId = activeDocument.id
    let cancelled = false

    async function hydrateConversation() {
      setIsHydrating(true)
      try {
        const conversations = await listConversations()
        const latestForDocument = conversations
          .filter((conv) => conv.document_id === activeDocumentId)
          .at(-1)

        if (!latestForDocument) {
          if (!cancelled) {
            setConversationId(null)
            setConversationDocumentId(null)
            setMessages(initialMessages())
            setLatestCitations([])
            setActiveCitationId(null)
          }
          return
        }

        const history = await listMessages(latestForDocument.id)
        if (!cancelled) {
          setConversationId(latestForDocument.id)
          setConversationDocumentId(activeDocumentId)
          setMessages(history.length > 0 ? history : initialMessages())
          const lastAssistant = [...history].reverse().find((m) => m.role === 'assistant')
          setLatestCitations(lastAssistant?.citations ?? [])
          setActiveCitationId(lastAssistant?.citations?.[0]?.id ?? null)
        }
      } catch {
        // fail silently
      } finally {
        if (!cancelled) setIsHydrating(false)
      }
    }

    void hydrateConversation()
    return () => {
      cancelled = true
    }
  }, [activeDocument?.id])

  function newChat() {
    setConversationId(null)
    setConversationDocumentId(null)
    setMessages(initialMessages())
    setLatestCitations([])
    setActiveCitationId(null)
  }

  const value = useMemo(
    () => ({
      conversationId,
      messages,
      latestCitations,
      activeCitationId,
      isSending: isSending || isHydrating,
      send,
      retry,
      activateCitationByLabel,
      newChat,
    }),
    [conversationId, messages, latestCitations, activeCitationId, isSending, isHydrating, activeDocument],
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
