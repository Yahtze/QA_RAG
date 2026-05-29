import type { RagDocument } from '@/types'

export const seededDocuments: RagDocument[] = [
  {
    id: 'doc-architecture',
    name: 'System Architecture Brief.pdf',
    type: 'PDF',
    sizeLabel: '1.8 MB',
    uploadedAt: 'Today, 9:12 AM',
    status: 'ready',
    progress: 100,
    summary: 'Architecture notes covering ingestion, chunking, retrieval, and answer generation.',
  },
  {
    id: 'doc-policy',
    name: 'Security Policy Draft.docx',
    type: 'DOCX',
    sizeLabel: '860 KB',
    uploadedAt: 'Today, 9:18 AM',
    status: 'processing',
    progress: 64,
    summary: 'Policy draft currently moving through chunking and embedding.',
  },
  {
    id: 'doc-failed',
    name: 'Legacy Export.txt',
    type: 'TXT',
    sizeLabel: '420 KB',
    uploadedAt: 'Yesterday, 4:03 PM',
    status: 'failed',
    progress: 22,
    summary: 'Import failed before embedding completed.',
    errorMessage: 'Document parser could not detect a valid text encoding.',
  },
]

export async function createUploadingDocument(file: File): Promise<RagDocument> {
  await delay(350)
  return {
    id: `doc-${Date.now()}`,
    name: file.name,
    type: file.name.split('.').pop()?.toUpperCase() ?? 'FILE',
    sizeLabel: formatBytes(file.size),
    uploadedAt: 'Just now',
    status: 'uploading',
    progress: 20,
    summary: 'Upload accepted. Preparing document for processing.',
  }
}

export async function processDocument(document: RagDocument, shouldFail: boolean): Promise<RagDocument> {
  await delay(650)
  if (shouldFail) {
    return {
      ...document,
      status: 'failed',
      progress: 35,
      summary: 'Processing failed before embeddings were created.',
      errorMessage: 'Simulated upload failure: worker could not complete processing.',
    }
  }

  await delay(850)
  return {
    ...document,
    status: 'ready',
    progress: 100,
    summary: 'Document indexed and ready for question answering.',
    errorMessage: undefined,
  }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
