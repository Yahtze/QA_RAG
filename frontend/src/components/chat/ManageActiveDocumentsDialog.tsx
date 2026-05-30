import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useActiveConversationScope } from '@/store/ActiveConversationScopeContext'
import { useConversation } from '@/store/ConversationContext'
import type { RagDocument } from '@/types'

interface Props {
  documents: RagDocument[]
  conversationId: string | null
}

export function ManageActiveDocumentsDialog({ documents, conversationId }: Props) {
  const scope = useActiveConversationScope()
  const conversation = useConversation()
  const [open, setOpen] = useState(false)

  return (
    <>
      <div className="rounded-xl border border-border/70 bg-card/60 p-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold">Selected Documents</p>
          <Button variant="outline" onClick={() => setOpen(true)}>
            Manage
          </Button>
        </div>
      </div>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-border bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-border/70 px-5 py-4">
              <h3 className="text-base font-semibold">Selected Documents</h3>
              <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
                Close
              </Button>
            </div>

            <div className="max-h-[60vh] space-y-2 overflow-y-auto px-5 py-4">
              {documents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
              ) : (
                documents.map((doc) => {
                  const ready = doc.status === 'ready'
                  const checked = scope.activeDocumentIds.includes(doc.id)
                  return (
                    <button
                      key={doc.id}
                      type="button"
                      disabled={!ready}
                      onClick={() => scope.toggleDocument(doc.id)}
                      className="flex w-full items-center justify-between rounded-xl border border-border/70 bg-card/60 px-4 py-3 text-left transition hover:border-primary/60 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{doc.name}</p>
                        <p className="text-xs text-muted-foreground">{doc.type} · {doc.sizeLabel}</p>
                      </div>
                      <Badge variant={checked ? 'default' : 'secondary'}>
                        {ready ? (checked ? 'Selected' : 'Ready') : doc.status}
                      </Badge>
                    </button>
                  )
                })
              )}
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-border/70 px-5 py-4">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={async () => {
                  if (conversationId) {
                    await scope.save(conversationId)
                    await conversation.updateActiveDocumentIds(scope.activeDocumentIds)
                  }
                  setOpen(false)
                }}
              >
                Save Selected Documents
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
