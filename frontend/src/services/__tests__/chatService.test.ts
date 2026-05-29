import { afterEach, describe, expect, it, vi } from 'vitest'
import { createConversation, askQuestion } from '../chatService'
import type { RagDocument } from '@/types'

const baseDoc: RagDocument = {
  id: 'doc-1',
  name: 'report.pdf',
  type: 'application/pdf',
  sizeLabel: '2 KB',
  uploadedAt: 'Today',
  status: 'ready',
  progress: 100,
  summary: 'Ready',
}

describe('chatService', () => {
  afterEach(() => vi.restoreAllMocks())

  it('creates conversation and returns id', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ id: 'conv-1', document_id: 'doc-1', created_at: '2026-05-29T00:00:00Z' }),
        { status: 200 },
      ),
    )

    const id = await createConversation('doc-1')
    expect(id).toBe('conv-1')
  })

  it('sends message and maps response to ChatResponse with citations', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          user_message: { id: 'm1', role: 'user', content: 'What is this?', created_at: '...', citations: [] },
          assistant_message: {
            id: 'm2',
            role: 'assistant',
            content: 'This is a document about X.',
            created_at: '...',
            citations: [
              { id: 'c1', document_id: 'doc-1', chunk_text: 'X is important.', page_number: 3, score: 0.95 },
            ],
          },
        }),
        { status: 200 },
      ),
    )

    const result = await askQuestion('conv-1', baseDoc, 'What is this?')

    expect(result.answer).toBe('This is a document about X.')
    expect(result.citations).toHaveLength(1)
    expect(result.citations[0]).toMatchObject({
      id: 'c1',
      documentId: 'doc-1',
      documentName: 'report.pdf',
      page: 3,
      snippet: 'X is important.',
    })
  })

  it('handles null page_number in citation', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          user_message: { id: 'm1', role: 'user', content: 'q', created_at: '...', citations: [] },
          assistant_message: {
            id: 'm2',
            role: 'assistant',
            content: 'Answer.',
            created_at: '...',
            citations: [
              { id: 'c1', document_id: 'doc-1', chunk_text: 'Key text.', page_number: null, score: 0.8 },
            ],
          },
        }),
        { status: 200 },
      ),
    )

    const result = await askQuestion('conv-1', baseDoc, 'q')
    expect(result.citations[0]!.page).toBe(1)
  })
})
