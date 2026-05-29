import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useSession } from '@/store/SessionContext'

export function TopBar() {
  const session = useSession()
  return (
    <header className="flex items-center justify-between border-b border-border/70 bg-card/50 px-6 py-4 backdrop-blur">
      <div>
        <h1 className="text-lg font-semibold tracking-tight">QA RAG Workspace</h1>
        <p className="text-sm text-muted-foreground">Ask grounded questions over selected documents.</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden text-sm text-muted-foreground sm:inline">{session.user?.email}</span>
        <Separator orientation="vertical" className="h-6" />
        <Button variant="ghost" size="sm" onClick={session.logout}><LogOut className="mr-2 size-4" />Logout</Button>
      </div>
    </header>
  )
}
