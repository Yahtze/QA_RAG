import { AlertCircle, CheckCircle2, Clock3, UploadCloud } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import type { RagDocument } from '@/types'

interface DocumentCardProps {
  document: RagDocument
  isActive: boolean
  onSelect: () => void
  onRetry: () => void
  onDelete: () => void
}

export function DocumentCard({ document, isActive, onSelect, onRetry, onDelete }: DocumentCardProps) {
  const icon = document.status === 'ready' ? <CheckCircle2 className="size-4 text-emerald-400" /> : document.status === 'failed' ? <AlertCircle className="size-4 text-destructive" /> : document.status === 'uploading' ? <UploadCloud className="size-4 text-primary" /> : <Clock3 className="size-4 text-accent" />
  return (
    <Card className={cn('cursor-pointer border-border/70 bg-card/70 transition hover:border-primary/60', isActive && 'border-primary/80 shadow-lg shadow-cyan-950/30')} onClick={document.status === 'ready' ? onSelect : undefined}>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0"><p className="truncate font-medium">{document.name}</p><p className="text-xs text-muted-foreground">{document.type} · {document.sizeLabel} · {document.uploadedAt}</p></div>
          <Badge variant={document.status === 'failed' ? 'destructive' : 'secondary'} className="gap-1">{icon}{document.status}</Badge>
        </div>
        <Progress value={document.progress} />
        {document.errorMessage && <p className="text-xs text-muted-foreground">{document.errorMessage}</p>}
        <div className="flex gap-2">
          {document.status === 'failed' && <Button size="sm" variant="secondary" onClick={(event) => { event.stopPropagation(); onRetry() }}>Retry</Button>}
          <Button size="sm" variant="destructive" onClick={(event) => {
            event.stopPropagation()
            const ok = window.confirm('Delete this document permanently? This removes raw file and VectorDB data.')
            if (ok) onDelete()
          }}>Delete</Button>
        </div>
      </CardContent>
    </Card>
  )
}
