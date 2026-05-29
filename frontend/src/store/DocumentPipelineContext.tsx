import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { createUploadingDocument, processDocument, seededDocuments } from '@/services/documentService'
import type { RagDocument } from '@/types'
import { useSimulationProfile } from './SimulationProfileContext'

interface DocumentPipelineValue {
  documents: RagDocument[]
  activeDocument: RagDocument | null
  upload: (file: File) => Promise<void>
  retry: (documentId: string) => Promise<void>
  selectDocument: (documentId: string) => void
}

const DocumentPipelineContext = createContext<DocumentPipelineValue | null>(null)

export function DocumentPipelineProvider({ children }: { children: ReactNode }) {
  const simulation = useSimulationProfile()
  const [documents, setDocuments] = useState<RagDocument[]>(seededDocuments)
  const [activeDocumentId, setActiveDocumentId] = useState('doc-architecture')

  async function upload(file: File) {
    const uploading = await createUploadingDocument(file)
    setDocuments((current) => [uploading, ...current])
    const shouldFail = simulation.consumeUploadFailure()
    const processed = await processDocument(uploading, shouldFail)
    setDocuments((current) => current.map((doc) => doc.id === processed.id ? processed : doc))
    if (processed.status === 'ready') setActiveDocumentId(processed.id)
  }

  async function retry(documentId: string) {
    const current = documents.find((doc) => doc.id === documentId)
    if (!current) return
    const uploading: RagDocument = { ...current, status: 'uploading', progress: 20, errorMessage: undefined, summary: 'Retry accepted. Uploading document again.' }
    setDocuments((docs) => docs.map((doc) => doc.id === documentId ? uploading : doc))
    const processed = await processDocument(uploading, false)
    setDocuments((docs) => docs.map((doc) => doc.id === documentId ? processed : doc))
    setActiveDocumentId(processed.id)
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
