import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { listDocuments, uploadDocument } from '@/services/documentService'
import type { RagDocument } from '@/types'

interface DocumentPipelineValue {
  documents: RagDocument[]
  activeDocument: RagDocument | null
  upload: (file: File) => Promise<void>
  retry: (documentId: string) => Promise<void>
  selectDocument: (documentId: string) => void
}

const DocumentPipelineContext = createContext<DocumentPipelineValue | null>(null)

export function DocumentPipelineProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<RagDocument[]>([])
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null)

  useEffect(() => {
    listDocuments().then((docs) => {
      setDocuments(docs)
      if (!activeDocumentId && docs.length > 0) {
        const firstReady = docs.find((d) => d.status === 'ready')
        if (firstReady) setActiveDocumentId(firstReady.id)
      }
    }).catch(() => {
      // fail silently — documents stay empty
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function upload(file: File) {
    const doc = await uploadDocument(file)
    setDocuments((current) => [doc, ...current])
    if (doc.status === 'ready') setActiveDocumentId(doc.id)
  }

  async function retry(_documentId: string) {
    // no-op: kept for API compatibility
  }

  function selectDocument(documentId: string) {
    const selected = documents.find((doc) => doc.id === documentId)
    if (selected?.status === 'ready') setActiveDocumentId(documentId)
  }

  const activeDocument = documents.find((doc) => doc.id === activeDocumentId && doc.status === 'ready') ?? null

  const value = useMemo(() => ({ documents, activeDocument, upload, retry, selectDocument }), [documents, activeDocument])

  return <DocumentPipelineContext.Provider value={value}>{children}</DocumentPipelineContext.Provider>
}

export function useDocumentPipeline() {
  const value = useContext(DocumentPipelineContext)
  if (!value) throw new Error('useDocumentPipeline must be used within DocumentPipelineProvider')
  return value
}
