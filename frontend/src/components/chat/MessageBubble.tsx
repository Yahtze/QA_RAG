import { Fragment } from 'react'
import { Bot, RefreshCw, User } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

function renderContentWithCitationLinks(
  content: string,
  enableLinks: boolean,
  onActivateCitation: (label: string) => void,
) {
  const chunks = content.split(/(\[\d+\])/g)
  return chunks.map((chunk, index) => {
    const match = chunk.match(/^\[(\d+)\]$/)
    if (enableLinks && match) {
      return (
        <button
          key={`${chunk}-${index}`}
          type="button"
          onClick={(e) => { e.stopPropagation(); onActivateCitation(match[1]!) }}
          className="mx-0.5 rounded px-1 text-primary underline underline-offset-2 hover:text-primary/80"
        >
          {chunk}
        </button>
      )
    }
    return <Fragment key={`${chunk}-${index}`}>{chunk}</Fragment>
  })
}

export function MessageBubble({ message, selected, onRetry, onSelect, onActivateCitation }: { message: Message; selected?: boolean; onRetry: () => void; onSelect: () => void; onActivateCitation: (label: string) => void }) {
  const isUser = message.role === 'user'
  const hasCitations = !isUser && (message.citations?.length ?? 0) > 0
  return (
    <div className={cn('flex gap-3', isUser && 'justify-end')}>
      {!isUser && <Avatar><AvatarFallback><Bot className="size-4" /></AvatarFallback></Avatar>}
      <div
        className={cn(
          'max-w-[80%] rounded-2xl border px-4 py-3 text-sm',
          isUser
            ? 'border-primary/50 bg-primary text-primary-foreground'
            : cn('border-border bg-card', hasCitations && 'cursor-pointer hover:border-primary/60 transition-colors', selected && 'border-primary ring-1 ring-primary/30'),
        )}
        onClick={!isUser && hasCitations ? onSelect : undefined}
        role={!isUser && hasCitations ? 'button' : undefined}
        tabIndex={!isUser && hasCitations ? 0 : undefined}
        onKeyDown={!isUser && hasCitations ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect() } } : undefined}
      >
        {message.status === 'loading' ? <div className="space-y-2"><Skeleton className="h-4 w-56" /><Skeleton className="h-4 w-40" /></div> : <p>{renderContentWithCitationLinks(message.content, !isUser, onActivateCitation)}</p>}
        {message.status === 'failed' && message.error?.retryable && <Button className="mt-3" size="sm" variant="secondary" onClick={onRetry}><RefreshCw className="mr-2 size-4" />Retry</Button>}
      </div>
      {isUser && <Avatar><AvatarFallback><User className="size-4" /></AvatarFallback></Avatar>}
    </div>
  )
}
