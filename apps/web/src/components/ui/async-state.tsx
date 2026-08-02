import { AlertTriangle, Inbox, RotateCcw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Skeleton } from '@/components/ui/skeleton'
import { useTranslations } from 'next-intl'

export function LoadingState({ label }: { label?: string }) {
  const common = useTranslations('Common')
  const resolvedLabel = label ?? common('loading')
  return (
    <div className="space-y-3" role="status" aria-label={resolvedLabel}>
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-16 w-full" />
      <span className="sr-only">{resolvedLabel}</span>
    </div>
  )
}

export function ErrorState({ title, description, referenceId, onRetry }: {
  title: string
  description: string
  referenceId?: string
  onRetry?: () => void
}) {
  const common = useTranslations('Common')
  return (
    <div className="space-y-3">
      <InlineAlert tone="danger" title={title}>
        <p>{description}</p>
        {referenceId && <p className="technical-id mt-1">{common('reference')}: {referenceId}</p>}
      </InlineAlert>
      {onRetry && <Button variant="outline" size="sm" onClick={onRetry}><RotateCcw />{common('retry')}</Button>}
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
