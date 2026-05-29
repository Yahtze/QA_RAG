import { ChatInput } from '@/components/chat/ChatInput'
import { ChatThread } from '@/components/chat/ChatThread'
import { CitationPanel } from '@/components/chat/CitationPanel'
import { DocumentList } from '@/components/documents/DocumentList'
import { UploadPanel } from '@/components/documents/UploadPanel'
import { AppShell } from '@/components/layout/AppShell'
import { SimulationControls } from '@/components/layout/SimulationControls'
import { Separator } from '@/components/ui/separator'
import { ConversationProvider } from '@/store/ConversationContext'
import { DocumentPipelineProvider } from '@/store/DocumentPipelineContext'
import { SimulationProfileProvider } from '@/store/SimulationProfileContext'

export default function Chat() {
  return (
    <SimulationProfileProvider>
      <DocumentPipelineProvider>
        <ConversationProvider>
          <AppShell
            left={<><UploadPanel /><div><h2 className="mb-3 font-semibold">Documents</h2><DocumentList /></div></>}
            center={<div className="space-y-4"><ChatThread /><Separator /><ChatInput /><SimulationControls /></div>}
            right={<CitationPanel />}
          />
        </ConversationProvider>
      </DocumentPipelineProvider>
    </SimulationProfileProvider>
  )
}
