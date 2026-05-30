import { useState } from 'react'
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
import { ChevronDown, ChevronRight } from 'lucide-react'

function ChatBody() {
  const { documents } = useDocumentPipeline()
  const { conversationId } = useConversation()
  const [documentsOpen, setDocumentsOpen] = useState(false)

  return (
    <AppShell
      left={<>
        <UploadPanel />
        <div>
          <button
            onClick={() => setDocumentsOpen(!documentsOpen)}
            className="flex w-full items-center gap-1.5 mb-3 font-semibold text-left"
          >
            {documentsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            Documents
          </button>
          {documentsOpen && <DocumentList />}
        </div>
      </>}
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
