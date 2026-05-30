import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useActiveConversationScope } from '@/store/ActiveConversationScopeContext'
import type { RagDocument } from '@/types'

interface Props {
  documents: RagDocument[]
  conversationId: string | null
}

export function ManageActiveDocumentsDialog({ documents, conversationId }: Props) {
  const scope = useActiveConversationScope()
  const [open, setOpen] = useState(false)

  return (
    <div className="space-y-2 rounded border p-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Active documents</p>
        <Button variant="outline" onClick={() => setOpen((current) => !current)}>
          {open ? 'Hide' : 'Manage'}
        </Button>
      </div>

      {open ? (
        <div className="space-y-2">
          {documents.map((doc) => {
            const ready = doc.status === 'ready'
            const checked = scope.activeDocumentIds.includes(doc.id)
            return (
              <button
                key={doc.id}
                type="button"
                disabled={!ready}
                onClick={() => scope.toggleDocument(doc.id)}
                className="flex w-full items-center justify-between rounded border p-3 text-left disabled:opacity-50"
              >
                <span>{doc.name}</span>
                <Badge variant={checked ? 'default' : 'secondary'}>
                  {ready ? (checked ? 'Active' : 'Ready') : doc.status}
                </Badge>
              </button>
            )
          })}

          <Button
            disabled={!conversationId}
            onClick={() => (conversationId ? void scope.save(conversationId) : undefined)}
          >
            Save active documents
          </Button>
        </div>
      ) : null}
    </div>
  )
}
