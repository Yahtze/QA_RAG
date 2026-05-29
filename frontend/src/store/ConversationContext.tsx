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
