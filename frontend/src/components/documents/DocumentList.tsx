import { ScrollArea } from '@/components/ui/scroll-area'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'
import { DocumentCard } from './DocumentCard'

export function DocumentList() {
  const pipeline = useDocumentPipeline()
  return (
    <ScrollArea className="h-[420px] pr-3">
      <div className="space-y-3">
        {pipeline.documents.map((document) => (
          <DocumentCard key={document.id} document={document} isActive={pipeline.activeDocument?.id === document.id} onSelect={() => pipeline.selectDocument(document.id)} onRetry={() => void pipeline.retry(document.id)} />
        ))}
      </div>
    </ScrollArea>
  )
}
