import * as React from 'react'
import { cn } from '@/lib/utils'

function Avatar({ className, ...props }: React.ComponentProps<'span'>) {
  return <span className={cn('relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full bg-muted items-center justify-center', className)} {...props} />
}

function AvatarFallback({ className, ...props }: React.ComponentProps<'span'>) {
  return <span className={cn('flex h-full w-full items-center justify-center rounded-full', className)} {...props} />
}

export { Avatar, AvatarFallback }
