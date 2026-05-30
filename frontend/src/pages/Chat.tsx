import { ChatInput } from '@/components/chat/ChatInput'
import { ChatThread } from '@/components/chat/ChatThread'
import { CitationPanel } from '@/components/chat/CitationPanel'
import { ManageActiveDocumentsDialog } from '@/components/chat/ManageActiveDocumentsDialog'
import { DocumentList } from '@/components/documents/DocumentList'
import { UploadPanel } from '@/components/documents/UploadPanel'
import { AppShell } from '@/components/layout/AppShell'
import { Separator } from '@/components/ui/separator'
import { ConversationProvider, useConversation } from '@/store/ConversationContext'
import { DocumentPipelineProvider, useDocumentPipeline } from '@/store/DocumentPipelineContext'
import { ActiveConversationScopeProvider } from '@/store/ActiveConversationScopeContext'

function ChatBody() {
  const { documents } = useDocumentPipeline()
  const { conversationId } = useConversation()

  return (
    <AppShell
      left={<><UploadPanel /><div><h2 className="mb-3 font-semibold">Documents</h2><DocumentList /></div></>}
      center={
        <div className="space-y-4">
          <ManageActiveDocumentsDialog documents={documents} conversationId={conversationId} />
          <ChatThread />
          <Separator />
          <ChatInput />
        </div>
      }
      right={<CitationPanel />}
    />
  )
}

function ScopedConversation() {
  const { documents } = useDocumentPipeline()

  return (
    <ActiveConversationScopeProvider documents={documents}>
      <ConversationProvider>
        <ChatBody />
      </ConversationProvider>
    </ActiveConversationScopeProvider>
  )
}

export default function Chat() {
  return (
    <DocumentPipelineProvider>
      <ScopedConversation />
    </DocumentPipelineProvider>
  )
}
