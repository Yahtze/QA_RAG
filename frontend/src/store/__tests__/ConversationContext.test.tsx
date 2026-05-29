import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ConversationProvider, useConversation } from '../ConversationContext'
import { DocumentPipelineProvider, useDocumentPipeline } from '../DocumentPipelineContext'

const mockChatResponse = vi.hoisted(() => ({
  answer: 'Processing involves chunking documents and indexing them for retrieval.',
  citations: [
    { id: 'c1', documentId: 'doc-1', documentName: 'report.pdf', page: 2, snippet: 'Chunking splits documents.' },
    { id: 'c2', documentId: 'doc-1', documentName: 'report.pdf', page: 5, snippet: 'Indexing enables search.' },
  ],
}))

vi.mock('@/services/documentService', () => ({
  listDocuments: vi.fn().mockResolvedValue([
    {
      id: 'doc-1',
      name: 'report.pdf',
      type: 'application/pdf',
      sizeLabel: '2 KB',
      uploadedAt: 'Today',
      status: 'ready' as const,
      progress: 100,
      summary: 'Ready',
    },
  ]),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
}))

vi.mock('@/services/chatService', () => ({
  createConversation: vi.fn().mockResolvedValue('conv-1'),
  askQuestion: vi.fn().mockResolvedValue(mockChatResponse),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <DocumentPipelineProvider><ConversationProvider>{children}</ConversationProvider></DocumentPipelineProvider>
}

describe('Conversation module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('answers with citations for the active ready document', async () => {
    const { result } = renderHook(() => ({ conversation: useConversation(), pipeline: useDocumentPipeline() }), { wrapper })

    await waitFor(() => expect(result.current.pipeline.activeDocument?.id).toBe('doc-1'))

    await act(async () => { await result.current.conversation.send('How does processing work?') })

    await waitFor(() => expect(result.current.conversation.messages.some((m) => m.role === 'assistant' && m.status === 'sent')).toBe(true), { timeout: 3000 })
    expect(result.current.conversation.latestCitations).toHaveLength(2)
  })

  it('stores failed assistant message and retries original query', async () => {
    const chatServiceModule = await import('@/services/chatService')
    vi.mocked(chatServiceModule.askQuestion).mockRejectedValueOnce(new Error('Backend error'))

    const { result } = renderHook(() => ({ conversation: useConversation(), pipeline: useDocumentPipeline() }), { wrapper })

    await waitFor(() => expect(result.current.pipeline.activeDocument?.id).toBe('doc-1'))

    await act(async () => { await result.current.conversation.send('Trigger failure') })

    await waitFor(() => expect(result.current.conversation.messages.some((m) => m.status === 'failed')).toBe(true), { timeout: 3000 })
    const failed = result.current.conversation.messages.find((m) => m.status === 'failed')!
    expect(failed.error?.originalQuery).toBe('Trigger failure')

    vi.mocked(chatServiceModule.askQuestion).mockResolvedValue(mockChatResponse)
    await act(async () => { await result.current.conversation.retry(failed.id) })

    expect(vi.mocked(chatServiceModule.askQuestion)).toHaveBeenLastCalledWith('conv-1', expect.any(Object), 'Trigger failure')
    await waitFor(() => expect(result.current.conversation.messages.some((m) => m.role === 'assistant' && m.status === 'sent')).toBe(true), { timeout: 3000 })
  })
})
