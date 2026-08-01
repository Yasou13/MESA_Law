'use client'

import { CalendarDays, FileText } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'

import { useListTimelineEvents } from '@/api/endpoints/default/default'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { StatusBadge } from '@/components/ui/status-badge'
import type { AppLocale } from '@/lib/navigation'

export function Timeline({ matterId }: { matterId: string }) {
  const t = useTranslations('Timeline')
  const common = useTranslations('Common')
  const locale = useLocale() as AppLocale
  const timelineQuery = useListTimelineEvents(matterId)
  const events = timelineQuery.data ?? []

  if (timelineQuery.isLoading) return <LoadingState label={common('loading')} />
  if (timelineQuery.isError) return <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => timelineQuery.refetch()} />
  if (events.length === 0) return <NoDataState title={t('emptyTitle')} description={t('emptyDescription')} />

  return (
    <div>
      <p className="mb-5 flex items-center gap-2 text-xs text-foreground-secondary"><CalendarDays className="size-4" />{t('events', { count: events.length })}</p>
      <ol className="relative ml-2 space-y-5 border-l border-border-strong">
        {events.map((event) => (
          <li key={event.id} className="relative pl-7">
            <span className="absolute -left-[5px] top-2 size-2.5 rounded-full border-2 border-surface bg-primary" aria-hidden="true" />
            <article className="rounded-lg border border-border bg-surface p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0"><time dateTime={event.date} className="text-xs font-medium text-primary">{new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(new Date(event.date))}</time><h2 className="mt-1 break-words font-semibold">{event.title}</h2></div>
                <StatusBadge status={event.confidence.toLowerCase() === 'high' ? 'verified' : 'warning'} label={`${t('confidence')}: ${event.confidence}`} />
              </div>
              {event.description && <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-foreground-secondary">{event.description}</p>}
              <p className="mt-3 flex items-center gap-2 text-xs text-foreground-muted"><FileText className="size-3.5" />{t('source')}: <span className="technical-id break-all">{event.source}</span></p>
            </article>
          </li>
        ))}
      </ol>
    </div>
  )
}
