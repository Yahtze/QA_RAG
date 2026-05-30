import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useDocumentPipeline } from '@/store/DocumentPipelineContext'

export function UploadPanel() {
  const pipeline = useDocumentPipeline()
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function upload() {
    if (!file) return
    setIsUploading(true)
    await pipeline.upload(file)
    setFile(null)
    setIsUploading(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null)
  }

  function triggerFileSelect() {
    fileInputRef.current?.click()
  }

  return (
    <Card className="border-border/70 bg-card/70">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><UploadCloud className="size-4 text-primary" />Upload Document</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileChange} />
        <Button type="button" variant="outline" className="w-full" onClick={triggerFileSelect}>Choose File</Button>
        <Button className="w-full" disabled={!file || isUploading} onClick={() => void upload()}>{isUploading ? 'Uploading…' : 'Upload'}</Button>
      </CardContent>
    </Card>
  )
}
