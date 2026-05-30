import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { deleteDocument, listDocuments, uploadDocument, uploadDocumentsBatch, type BatchUploadSummary } from '@/services/documentService'
import type { RagDocument } from '@/types'

interface DocumentPipelineValue {
  documents: RagDocument[]
  activeDocument: RagDocument | null
  upload: (file: File) => Promise<void>
  uploadBatch: (files: File[]) => Promise<BatchUploadSummary>
  retry: (documentId: string) => Promise<void>
  remove: (documentId: string) => Promise<void>
  selectDocument: (documentId: string) => void
}

const POLL_INTERVAL_MS = 2000
const ACTIVE_DOCUMENT_STORAGE_KEY = 'qa-rag:active-document-id'

function readStoredActiveDocumentId(): string | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    return window.localStorage.getItem(ACTIVE_DOCUMENT_STORAGE_KEY)
  } catch {
    return null
  }
}

function writeStoredActiveDocumentId(value: string | null): void {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return
    if (value) {
      window.localStorage.setItem(ACTIVE_DOCUMENT_STORAGE_KEY, value)
    } else {
      window.localStorage.removeItem(ACTIVE_DOCUMENT_STORAGE_KEY)
    }
  } catch {
    // no-op
  }
}

const DocumentPipelineContext = createContext<DocumentPipelineValue | null>(null)

export function DocumentPipelineProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<RagDocument[]>([])
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(readStoredActiveDocumentId)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current !== null) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const refreshDocs = useCallback(() => {
    listDocuments().then((docs) => {
      setDocuments(docs)
      const hasActive = activeDocumentId && docs.some((d) => d.id === activeDocumentId && d.status === 'ready')
      if (!hasActive) {
        const firstReady = docs.find((d) => d.status === 'ready')
        setActiveDocumentId(firstReady?.id ?? null)
      }
      const nonReady = docs.filter((d) => d.status !== 'ready' && d.status !== 'failed')
      if (nonReady.length === 0) stopPolling()
    }).catch(() => {
      // fail silently
    })
  }, [activeDocumentId, stopPolling])

  const startPolling = useCallback(() => {
    stopPolling()
    pollingRef.current = setInterval(refreshDocs, POLL_INTERVAL_MS)
  }, [refreshDocs, stopPolling])

  useEffect(() => {
    refreshDocs()
    return stopPolling
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function upload(file: File) {
    const doc = await uploadDocument(file)
    setDocuments((current) => [doc, ...current])
    startPolling()
    if (doc.status === 'ready') setActiveDocumentId(doc.id)
  }

  async function uploadBatch(files: File[]): Promise<BatchUploadSummary> {
    const summary = await uploadDocumentsBatch(files)
    const acceptedDocs = summary.results
      .filter((result) => result.status === 'accepted' && result.document)
      .map((result) => result.document as RagDocument)

    if (acceptedDocs.length > 0) {
      setDocuments((current) => [...acceptedDocs, ...current])
      startPolling()
      if (acceptedDocs[0]?.status === 'ready') setActiveDocumentId(acceptedDocs[0].id)
    }

    return summary
  }

  async function retry(documentId: string) {
    void documentId
    // no-op: kept for API compatibility
  }

  async function remove(documentId: string) {
    await deleteDocument(documentId)
    setDocuments((current) => current.filter((doc) => doc.id !== documentId))
    setActiveDocumentId((current) => (current === documentId ? null : current))
  }

  function selectDocument(documentId: string) {
    const selected = documents.find((doc) => doc.id === documentId)
    if (selected?.status === 'ready') setActiveDocumentId(documentId)
  }

  useEffect(() => {
    writeStoredActiveDocumentId(activeDocumentId)
  }, [activeDocumentId])

  const activeDocument = documents.find((doc) => doc.id === activeDocumentId && doc.status === 'ready') ?? null

  const value = useMemo(() => ({ documents, activeDocument, upload, uploadBatch, retry, remove, selectDocument }), [documents, activeDocument])

  return <DocumentPipelineContext.Provider value={value}>{children}</DocumentPipelineContext.Provider>
}

export function useDocumentPipeline() {
  const value = useContext(DocumentPipelineContext)
  if (!value) throw new Error('useDocumentPipeline must be used within DocumentPipelineProvider')
  return value
}
