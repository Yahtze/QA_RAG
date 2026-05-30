import { afterEach, describe, expect, it, vi } from 'vitest'
import { listDocuments, uploadDocument, deleteDocument, mapDocument } from '../documentService'

const baseDoc = {
  id: 'doc-1',
  filename: 'report.pdf',
  content_type: 'application/pdf',
  size_bytes: 2048,
  status: 'ready' as const,
  error_message: null,
  created_at: '2026-05-29T00:00:00Z',
  updated_at: '2026-05-29T00:00:00Z',
}

describe('documentService', () => {
  afterEach(() => vi.restoreAllMocks())

  it('maps DocumentOut to RagDocument', () => {
    const result = mapDocument(baseDoc)
    expect(result).toMatchObject({
      id: 'doc-1',
      name: 'report.pdf',
      type: 'application/pdf',
      status: 'ready',
      progress: 100,
    })
    expect(result.sizeLabel).toBe('2 KB')
  })

  it('sets progress based on status', () => {
    expect(mapDocument({ ...baseDoc, status: 'uploading' }).progress).toBe(35)
    expect(mapDocument({ ...baseDoc, status: 'processing' }).progress).toBe(65)
    expect(mapDocument({ ...baseDoc, status: 'failed' }).progress).toBe(100)
  })

  it('uploads document via FormData', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          ...baseDoc,
          id: 'new-doc',
          filename: 'test.pdf',
          status: 'ready',
        }),
        { status: 200 },
      ),
    )

    const file = new File(['hello'], 'test.pdf', { type: 'application/pdf' })
    const result = await uploadDocument(file)

    expect(result.name).toBe('test.pdf')
    expect(result.status).toBe('ready')
  })

  it('lists documents from backend', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [baseDoc], page_info: { next_cursor: null, has_more: false } }), { status: 200 }),
    )

    const docs = await listDocuments()
    expect(docs).toHaveLength(1)
    expect(docs[0]!.name).toBe('report.pdf')
  })

  it('deletes document and returns void', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 204 }),
    )

    await expect(deleteDocument('doc-1')).resolves.toBeUndefined()
  })
})
