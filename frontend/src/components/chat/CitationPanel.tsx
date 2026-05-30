import { useEffect } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { CitationCard } from './CitationCard'

export function CitationPanel() {
  const conversation = useConversation()

  useEffect(() => {
    if (!conversation.activeCitationId) return
    const el = document.getElementById(`citation-${conversation.activeCitationId}`)
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [conversation.activeCitationId])

  return (
    <aside className="space-y-3">
      <div><h2 className="font-semibold">Sources</h2><p className="text-sm text-muted-foreground">Latest answer citations.</p></div>
      <ScrollArea className="h-[70vh] rounded-xl border border-border/60 bg-card/40 p-3 pr-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-muted-foreground/30 hover:[&::-webkit-scrollbar-thumb]:bg-muted-foreground/50 [&::-webkit-scrollbar-track]:bg-transparent">
        <div className="space-y-3">
          {conversation.latestCitations.length === 0 ? <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">Ask a question to populate citations.</p> : conversation.latestCitations.map((citation) => <CitationCard key={citation.id} citation={citation} active={conversation.activeCitationId === citation.id} />)}
        </div>
      </ScrollArea>
    </aside>
  )
}
