import { Bot, RefreshCw, User } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

export function MessageBubble({ message, onRetry }: { message: Message; onRetry: () => void }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-3', isUser && 'justify-end')}>
      {!isUser && <Avatar><AvatarFallback><Bot className="size-4" /></AvatarFallback></Avatar>}
      <div className={cn('max-w-[80%] rounded-2xl border px-4 py-3 text-sm', isUser ? 'border-primary/50 bg-primary text-primary-foreground' : 'border-border bg-card')}>
        {message.status === 'loading' ? <div className="space-y-2"><Skeleton className="h-4 w-56" /><Skeleton className="h-4 w-40" /></div> : <p>{message.content}</p>}
        {message.status === 'failed' && message.error?.retryable && <Button className="mt-3" size="sm" variant="secondary" onClick={onRetry}><RefreshCw className="mr-2 size-4" />Retry</Button>}
      </div>
      {isUser && <Avatar><AvatarFallback><User className="size-4" /></AvatarFallback></Avatar>}
    </div>
  )
}
