import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Citation } from '@/types'

export function CitationCard({ citation, active }: { citation: Citation; active?: boolean }) {
  return (
    <Card id={`citation-${citation.id}`} className={cn(active ? 'border-primary bg-primary/5' : 'border-border/70 bg-card/70', 'overflow-hidden')}>
      <CardHeader className="pb-2"><CardTitle className="text-sm">Source: page {citation.page}</CardTitle></CardHeader>
      <CardContent><p className="truncate text-xs text-muted-foreground">{citation.documentName}</p><p className="mt-2 break-words text-sm">{citation.snippet}</p></CardContent>
    </Card>
  )
}
