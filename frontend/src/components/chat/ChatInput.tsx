import { FormEvent, KeyboardEvent, useState } from 'react'
import { SendHorizonal } from 'lucide-react'
import { useConversation } from '@/store/ConversationContext'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function ChatInput() {
  const conversation = useConversation()
  const pipeline = useDocumentPipeline()
  const [query, setQuery] = useState('')
  const [focused, setFocused] = useState(false)

  async function handleSend(value: string) {
    if (!value.trim()) return
    setQuery('')
    await conversation.send(value.trim())
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(query)
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    handleSend(query)
  }

  function onChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setQuery(e.target.value)
  }

  return (
    <form onSubmit={onSubmit}>
      <div className={`relative rounded-2xl border bg-card shadow-lg transition-all duration-200 ${focused ? 'border-primary/50 ring-2 ring-primary/20 shadow-primary/15' : 'border-border/70'}`}>
        <textarea
          value={query}
          onChange={onChange}
          onKeyDown={onKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={''}
          disabled={!pipeline.activeDocument || conversation.isSending}
          rows={3}
          className="w-full resize-none rounded-2xl bg-transparent px-5 py-4 pr-14 text-sm outline-none placeholder:text-muted-foreground/60 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <div className="absolute bottom-3 right-3">
          <button
            type="submit"
            disabled={!pipeline.activeDocument || conversation.isSending || !query.trim()}
            className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm transition-all hover:bg-primary/90 hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <SendHorizonal className="size-5" />
          </button>
        </div>
      </div>
    </form>
  )
}
