import React from 'react'
import { FolderOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { clsx } from 'clsx'

interface EmptyStateProps {
  icon?: React.ElementType
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  icon: Icon = FolderOpen,
  title,
  description,
  actionLabel,
  onAction,
  className
}: EmptyStateProps) {
  return (
    <div className={clsx(
      "flex flex-col items-center justify-center rounded-lg border border-dashed border-border-strong bg-surface p-10 text-center",
      className
    )}>
      <div className="mb-5 flex size-10 items-center justify-center rounded-lg bg-surface-subtle">
        <Icon className="size-5 text-foreground-secondary" aria-hidden="true" />
      </div>
      
      <h3 className="mb-1 text-base font-semibold text-foreground">
        {title}
      </h3>
      
      {description && (
        <p className="mb-5 max-w-md text-sm text-foreground-secondary">
          {description}
        </p>
      )}
      
      {actionLabel && onAction && (
        <Button 
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
