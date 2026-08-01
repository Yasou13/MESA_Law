import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

export function Panel({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cn('rounded-lg border border-border bg-surface', className)}
      {...props}
    />
  )
}

export function PanelHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex min-h-12 items-center justify-between gap-4 border-b border-border-subtle px-4 py-3', className)}
      {...props}
    />
  )
}

export function PanelBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-4', className)} {...props} />
}
