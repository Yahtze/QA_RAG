import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { MessageBubble } from './MessageBubble'

export function ChatThread() {
  const conversation = useConversation()
  return (
    <ScrollArea className="h-[58vh] pr-4 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-muted-foreground/30 hover:[&::-webkit-scrollbar-thumb]:bg-muted-foreground/50 [&::-webkit-scrollbar-track]:bg-transparent">
      <div className="space-y-5">
        {conversation.messages.map((message) => <MessageBubble key={message.id} message={message} selected={conversation.selectedMessageId === message.id} onRetry={() => void conversation.retry(message.id)} onSelect={() => conversation.selectMessage(message.id)} onActivateCitation={conversation.activateCitationByLabel} />)}
      </div>
    </ScrollArea>
  )
}
