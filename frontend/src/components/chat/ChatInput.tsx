import { FormEvent, useState } from 'react'
import { SendHorizonal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useConversation } from '@/store/ConversationContext'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function ChatInput() {
  const conversation = useConversation()
  const pipeline = useDocumentPipeline()
  const [query, setQuery] = useState('What does this document say about the RAG pipeline?')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const value = query.trim()
    if (!value) return
    setQuery('')
    await conversation.send(value)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <Textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder={pipeline.activeDocument ? 'Ask a question about the selected document…' : 'Select a ready document first…'} disabled={!pipeline.activeDocument || conversation.isSending} />
      <Button type="submit" disabled={!pipeline.activeDocument || conversation.isSending || !query.trim()}><SendHorizonal className="mr-2 size-4" />Send</Button>
    </form>
  )
}
