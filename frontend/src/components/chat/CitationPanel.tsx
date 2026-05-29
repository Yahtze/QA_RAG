import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { CitationCard } from './CitationCard'

export function CitationPanel() {
  const conversation = useConversation()
  return (
    <aside className="space-y-3">
      <div><h2 className="font-semibold">Sources</h2><p className="text-sm text-muted-foreground">Latest answer citations.</p></div>
      <ScrollArea className="h-[70vh] pr-3">
        <div className="space-y-3">
          {conversation.latestCitations.length === 0 ? <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">Ask a question to populate citations.</p> : conversation.latestCitations.map((citation) => <CitationCard key={citation.id} citation={citation} />)}
        </div>
      </ScrollArea>
    </aside>
  )
}
