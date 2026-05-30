import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversation } from '@/store/ConversationContext'
import { MessageBubble } from './MessageBubble'

export function ChatThread() {
  const conversation = useConversation()
  return (
    <ScrollArea className="h-[58vh] pr-4">
      <div className="space-y-5">
        {conversation.messages.map((message) => <MessageBubble key={message.id} message={message} onRetry={() => void conversation.retry(message.id)} onActivateCitation={conversation.activateCitationByLabel} />)}
      </div>
    </ScrollArea>
  )
}
