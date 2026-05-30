import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import { ConversationProvider, useConversation } from '../ConversationContext'
import { DocumentPipelineProvider, useDocumentPipeline } from '../DocumentPipelineContext'

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
}))

vi.mock('@/services/conversationStream', () => ({
  streamConversationMessage: vi.fn(),
}))

import { streamConversationMessage } from '@/services/conversationStream'

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <DocumentPipelineProvider>
      <ConversationProvider>{children}</ConversationProvider>
    </DocumentPipelineProvider>
  )
}

async function selectReadyDocument(result: {
  current: { pipeline: ReturnType<typeof useDocumentPipeline> }
}) {
  await waitFor(() => expect(result.current.pipeline.documents.length).toBeGreaterThan(0))
  act(() => {
    result.current.pipeline.selectDocument('doc-1')
  })
  await waitFor(() => expect(result.current.pipeline.activeDocument?.id).toBe('doc-1'))
}

describe('Conversation module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('appends streamed tokens and citations to assistant message', async () => {
    vi.mocked(streamConversationMessage).mockImplementation(
      async function* () {
        yield { type: 'token', value: 'Hello ' }
        yield { type: 'token', value: 'world [1].' }
        yield {
          type: 'citations',
          map: {
            '1': {
              chunkId: 'c1',
              docId: 'd1',
              filename: 'guide.pdf',
              page: 2,
              snippet: 'world',
            },
          },
        }
        yield { type: 'done' }
      },
    )

    const { result } = renderHook(
      () => ({ conversation: useConversation(), pipeline: useDocumentPipeline() }),
      { wrapper },
    )

    await selectReadyDocument(result)

    await act(async () => {
      await result.current.conversation.send('q')
    })

    await waitFor(
      () =>
        expect(
          result.current.conversation.messages.some(
            (m) => m.role === 'assistant' && m.status === 'sent' && m.content === 'Hello world [1].',
          ),
        ).toBe(true),
      { timeout: 3000 },
    )

    const assistant = result.current.conversation.messages.find(
      (m) => m.role === 'assistant' && m.content === 'Hello world [1].',
    )
    expect(assistant?.citations?.[0]?.documentName).toBe('guide.pdf')
  })

  it('keeps only citations referenced in assistant text', async () => {
    vi.mocked(streamConversationMessage).mockImplementation(
      async function* () {
        yield { type: 'token', value: 'Answer cites only [1].' }
        yield {
          type: 'citations',
          map: {
            '1': {
              chunkId: 'c1',
              docId: 'd1',
              filename: 'guide.pdf',
              page: 2,
              snippet: 'used citation',
            },
            '2': {
              chunkId: 'c2',
              docId: 'd1',
              filename: 'guide.pdf',
              page: 3,
              snippet: 'unused citation',
            },
          },
        }
        yield { type: 'done' }
      },
    )

    const { result } = renderHook(
      () => ({ conversation: useConversation(), pipeline: useDocumentPipeline() }),
      { wrapper },
    )

    await selectReadyDocument(result)

    await act(async () => {
      await result.current.conversation.send('q')
    })

    await waitFor(
      () => expect(result.current.conversation.latestCitations).toHaveLength(1),
      { timeout: 3000 },
    )

    expect(result.current.conversation.latestCitations[0]?.label).toBe('1')
  })

  it('marks assistant failed on error event', async () => {
    vi.mocked(streamConversationMessage).mockImplementation(
      async function* () {
        yield {
          type: 'error',
          message: 'LLM configuration is missing.',
          retryable: true,
        }
      },
    )

    const { result } = renderHook(
      () => ({ conversation: useConversation(), pipeline: useDocumentPipeline() }),
      { wrapper },
    )

    await selectReadyDocument(result)

    await act(async () => {
      await result.current.conversation.send('q')
    })

    await waitFor(
      () => expect(result.current.conversation.messages.some((m) => m.status === 'failed')).toBe(true),
      { timeout: 3000 },
    )

    const failed = result.current.conversation.messages.find((m) => m.status === 'failed')
    expect(failed?.error?.originalQuery).toBe('q')
  })
})
