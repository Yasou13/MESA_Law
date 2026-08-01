import { AlertTriangle, Inbox, RotateCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Skeleton } from '@/components/ui/skeleton'

export function LoadingState({ label = 'Yükleniyor' }: { label?: string }) {
  return (
    <div className="space-y-3" role="status" aria-label={label}>
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
      <span className="sr-only">{label}</span>
    </div>
  )
}

export function ErrorState({ title, description, referenceId, onRetry }: {
  title: string
  description: string
  referenceId?: string
  onRetry?: () => void
}) {
  return (
    <div className="space-y-3">
      <InlineAlert tone="danger" title={title}>
        <p>{description}</p>
        {referenceId && <p className="technical-id mt-1">Referans: {referenceId}</p>}
      </InlineAlert>
      {onRetry && <Button variant="outline" size="sm" onClick={onRetry}><RotateCcw />Yeniden dene</Button>}
    </div>
  )
}

export function DegradedState({ title, description }: { title: string; description: string }) {
  return <InlineAlert tone="warning" title={title}><p>{description}</p></InlineAlert>
}

export function NoDataState({ title, description, actionLabel, onAction }: {
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}) {
  return <EmptyState icon={Inbox} title={title} description={description} actionLabel={actionLabel} onAction={onAction} />
}

export function FailureIcon() {
  return <AlertTriangle className="size-5" aria-hidden="true" />
}
