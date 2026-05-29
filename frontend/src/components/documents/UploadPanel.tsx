import { useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function UploadPanel() {
  const pipeline = useDocumentPipeline()
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  async function upload() {
    if (!file) return
    setIsUploading(true)
    await pipeline.upload(file)
    setFile(null)
    setIsUploading(false)
  }

  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UploadCloud className="size-4 text-primary" />Upload document</CardTitle><CardDescription>Fake upload pipeline with processing states.</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Label htmlFor="document-upload">Document file</Label>
        <Input id="document-upload" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <Button className="w-full" disabled={!file || isUploading} onClick={() => void upload()}>{isUploading ? 'Uploading…' : 'Upload'}</Button>
      </CardContent>
    </Card>
  )
}
