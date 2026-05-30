import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function UploadPanel() {
  const pipeline = useDocumentPipeline()
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function upload() {
    if (files.length === 0) return
    setIsUploading(true)
    await pipeline.uploadBatch(files)
    setFiles([])
    setIsUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(e.target.files ?? []))
  }

  function triggerFileSelect() {
    fileInputRef.current?.click()
  }

  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UploadCloud className="size-4 text-primary" />Upload Documents</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleFileChange} />
        <Button type="button" variant="outline" className="w-full" onClick={triggerFileSelect}>Choose Files</Button>
        {files.length > 0 && <p className="text-xs text-muted-foreground">{files.length} file(s) selected</p>}
        <Button className="w-full" disabled={files.length === 0 || isUploading} onClick={() => void upload()}>{isUploading ? 'Uploading…' : 'Upload'}</Button>
      </CardContent>
    </Card>
  )
}
