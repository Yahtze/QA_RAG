import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { DocumentPipelineProvider, useDocumentPipeline } from '../DocumentPipelineContext'

const mockDocs = vi.hoisted(() => [
  {
    id: 'doc-1',
    name: 'existing.pdf',
    type: 'application/pdf',
    sizeLabel: '1 KB',
    uploadedAt: 'Today',
    status: 'ready' as const,
    progress: 100,
    summary: 'Ready',
  },
])

vi.mock('@/services/documentService', () => ({
  listDocuments: vi.fn().mockResolvedValue(mockDocs),
  uploadDocument: vi.fn().mockImplementation((file: File) =>
    Promise.resolve({
      id: 'doc-uploaded',
      name: file.name,
      type: 'application/pdf',
      sizeLabel: '5 KB',
      uploadedAt: 'Just now',
      status: 'ready' as const,
      progress: 100,
      summary: 'Document ready for questions.',
    }),
  ),
  deleteDocument: vi.fn().mockResolvedValue(undefined),
}))

describe('DocumentPipelineContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads documents on mount', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), {
      wrapper: DocumentPipelineProvider,
    })
    await waitFor(() => expect(result.current.documents).toEqual(mockDocs))
  })

  it('uploads a document and adds it to list', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), {
      wrapper: DocumentPipelineProvider,
    })
    await waitFor(() => expect(result.current.documents).toHaveLength(1))

    const file = new File(['hello'], 'new.pdf', { type: 'application/pdf' })
    await act(async () => {
      await result.current.upload(file)
    })

    expect(result.current.documents).toHaveLength(2)
    expect(result.current.documents[0]!.name).toBe('new.pdf')
  })

  it('selects uploaded ready document', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), {
      wrapper: DocumentPipelineProvider,
    })
    await waitFor(() => expect(result.current.documents).toHaveLength(1))

    const file = new File(['hello'], 'selectable.pdf', { type: 'application/pdf' })
    await act(async () => {
      await result.current.upload(file)
    })

    expect(result.current.activeDocument?.name).toBe('selectable.pdf')
  })

  it('retry is a no-op and does not throw', async () => {
    const { result } = renderHook(() => useDocumentPipeline(), {
      wrapper: DocumentPipelineProvider,
    })
    await waitFor(() => expect(result.current.documents).toHaveLength(1))

    await act(async () => {
      await result.current.retry('non-existent')
    })
    // Should not throw
  })
})
