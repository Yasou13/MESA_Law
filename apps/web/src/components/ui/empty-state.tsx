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
      "flex flex-col items-center justify-center p-12 text-center",
      "glass-card border border-[var(--border-surface)] border-dashed rounded-xl",
      className
    )}>
      <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-6">
        <Icon className="w-8 h-8 text-[var(--color-anthracite-400)]" />
      </div>
      
      <h3 className="text-xl font-semibold text-[var(--foreground)] tracking-tight mb-2">
        {title}
      </h3>
      
      {description && (
        <p className="text-[var(--color-anthracite-500)] max-w-sm mb-6">
          {description}
        </p>
      )}
      
      {actionLabel && onAction && (
        <Button 
          onClick={onAction}
          className="bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
