import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Citation } from '@/types'

export function CitationCard({ citation }: { citation: Citation }) {
  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader className="pb-2"><CardTitle className="text-sm">Source: page {citation.page}</CardTitle></CardHeader>
      <CardContent><p className="text-xs text-muted-foreground">{citation.documentName}</p><p className="mt-2 text-sm">{citation.snippet}</p></CardContent>
    </Card>
  )
}
