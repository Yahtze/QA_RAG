import { cn } from '@/lib/utils'

export function ScrollArea({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn('overflow-y-auto overflow-x-hidden', className)}>{children}</div>
}
