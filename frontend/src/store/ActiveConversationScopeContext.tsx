import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

import { updateActiveDocuments } from '@/services/chatService'
import type { RagDocument } from '@/types'

interface ActiveConversationScopeValue {
  activeDocumentIds: string[]
  activeDocuments: RagDocument[]
  readyDocuments: RagDocument[]
  toggleDocument: (documentId: string) => void
  setActiveDocumentIds: (ids: string[]) => void
  save: (conversationId: string) => Promise<void>
}

const ActiveConversationScopeContext = createContext<ActiveConversationScopeValue | null>(null)

interface Props {
  children: ReactNode
  documents: RagDocument[]
  saveActiveDocuments?: (conversationId: string, ids: string[]) => Promise<unknown>
}

export function ActiveConversationScopeProvider({
  children,
  documents,
  saveActiveDocuments = updateActiveDocuments,
}: Props) {
  const [activeDocumentIds, setActiveDocumentIds] = useState<string[]>([])
  const readyDocuments = documents.filter((doc) => doc.status === 'ready')
  const readyIds = new Set(readyDocuments.map((doc) => doc.id))
  const activeDocuments = readyDocuments.filter((doc) => activeDocumentIds.includes(doc.id))

  function toggleDocument(documentId: string) {
    if (!readyIds.has(documentId)) return
    setActiveDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    )
  }

  async function save(conversationId: string) {
    const ids = activeDocumentIds.filter((id) => readyIds.has(id))
    await saveActiveDocuments(conversationId, ids)
    setActiveDocumentIds(ids)
  }

  const value = useMemo(
    () => ({
      activeDocumentIds,
      activeDocuments,
      readyDocuments,
      toggleDocument,
      setActiveDocumentIds,
      save,
    }),
    [activeDocumentIds, activeDocuments, readyDocuments],
  )

  return (
    <ActiveConversationScopeContext.Provider value={value}>
      {children}
    </ActiveConversationScopeContext.Provider>
  )
}

export function useActiveConversationScope() {
  const value = useContext(ActiveConversationScopeContext)
  if (!value) {
    throw new Error('useActiveConversationScope must be used within ActiveConversationScopeProvider')
  }
  return value
}
