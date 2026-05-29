import { apiRequest } from './apiClient'
import type { RagDocument } from '@/types'

export interface DocumentOut {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  status: 'uploading' | 'processing' | 'ready' | 'failed'
  error_message: string | null
  created_at: string
  updated_at: string
}

export function mapDocument(doc: DocumentOut): RagDocument {
  const progressMap: Record<DocumentOut['status'], number> = {
    uploading: 35,
    processing: 65,
    ready: 100,
    failed: 100,
  }

  const summaryMap: Record<DocumentOut['status'], string> = {
    uploading: 'Uploading document...',
    processing: 'Processing document...',
    ready: 'Document ready for questions.',
    failed: doc.error_message ?? 'Document processing failed.',
  }

  return {
    id: doc.id,
    name: doc.filename,
    type: doc.content_type,
    sizeLabel: formatBytes(doc.size_bytes),
    uploadedAt: new Date(doc.created_at).toLocaleString(),
    status: doc.status,
    progress: progressMap[doc.status],
    summary: summaryMap[doc.status],
    errorMessage: doc.error_message ?? undefined,
  }
}

export async function listDocuments(): Promise<RagDocument[]> {
  const docs = await apiRequest<DocumentOut[]>('/documents')
  return docs.map(mapDocument)
}

export async function uploadDocument(file: File): Promise<RagDocument> {
  const formData = new FormData()
  formData.append('file', file)
  const doc = await apiRequest<DocumentOut>('/documents/upload', {
    method: 'POST',
    body: formData,
  })
  return mapDocument(doc)
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiRequest<void>(`/documents/${documentId}`, { method: 'DELETE' })
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
