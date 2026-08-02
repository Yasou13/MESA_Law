'use client'

import { AlertTriangle, ArrowRight, Bell, BriefcaseBusiness, CalendarClock, FileCheck2, Files, ShieldAlert } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'

import { useGetDashboardMetrics } from '@/api/endpoints/dashboard/dashboard'
import { useListAllDocuments, useListMatters } from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import { useListReviews } from '@/api/endpoints/reviews/reviews'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { StatusBadge } from '@/components/ui/status-badge'
import { localizedHref, type AppLocale } from '@/lib/navigation'

export default function DashboardPage() {
  const t = useTranslations('Dashboard')
  const common = useTranslations('Common')
  const locale = useLocale() as AppLocale
  const metricsQuery = useGetDashboardMetrics()
  const mattersQuery = useListMatters()
  const deadlinesQuery = useListDeadlines()
  const reviewsQuery = useListReviews({ status: 'PROPOSED' })
  const documentsQuery = useListAllDocuments()

  if (metricsQuery.isLoading) return <LoadingState label={common('loading')} />
  if (metricsQuery.isError) return <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => metricsQuery.refetch()} />

  const metrics = metricsQuery.data
  const matters = (mattersQuery.data ?? []).slice(0, 5)
  const deadlines = (deadlinesQuery.data ?? []).filter((deadline) => !deadline.is_completed).slice(0, 5)
  const reviews = (reviewsQuery.data ?? []).slice(0, 5)
  const processedDocuments = (documentsQuery.data ?? []).filter((document) => ['clean', 'ready', 'processed'].includes(document.status.toLowerCase())).length

  const priorities = [
    { label: t('activeMatters'), value: metrics?.active_matters ?? 0, icon: BriefcaseBusiness, href: '/matters', tone: 'text-info' },
    { label: t('pendingReviews'), value: metrics?.pending_reviews ?? 0, icon: Files, href: '/reviews', tone: 'text-review' },
    { label: t('processedDocuments'), value: processedDocuments, icon: FileCheck2, href: '/documents', tone: 'text-verified' },
    { label: t('failedOperations'), value: metrics?.failed_operations ?? 0, icon: ShieldAlert, href: '/operations', tone: 'text-danger' },
    { label: t('upcomingDeadlines'), value: metrics?.upcoming_deadlines ?? 0, icon: CalendarClock, href: '/deadlines', tone: 'text-warning' },
    { label: t('unreadNotifications'), value: metrics?.unread_notifications ?? 0, icon: Bell, href: '/notifications', tone: 'text-foreground-secondary' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />

      {metrics?.system_status === 'degraded' && (
        <div className="flex gap-3 rounded-lg border border-warning/30 bg-warning-soft p-4 text-sm" role="status">
          <AlertTriangle className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden="true" />
          <div><p className="font-semibold text-warning">{t('degradedTitle')}</p><p className="mt-1 text-foreground-secondary">{t('degradedDescription', { capabilities: metrics.degraded_capabilities.join(', ') })}</p></div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {priorities.map((priority) => (
          <Link key={priority.label} href={localizedHref(locale, priority.href)} className="rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus">
            <Panel className="h-full transition-colors hover:border-border-strong">
              <PanelBody className="flex items-center justify-between">
                <div><p className="text-xs font-medium text-foreground-secondary">{priority.label}</p><p className="mt-1 text-3xl font-semibold tabular-nums">{priority.value}</p></div>
                <priority.icon className={`size-5 ${priority.tone}`} aria-hidden="true" />
              </PanelBody>
            </Panel>
          </Link>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel>
          <PanelHeader><h2 className="font-semibold">{t('activeMatters')}</h2><ViewAll locale={locale} href="/matters" label={t('viewAll')} /></PanelHeader>
          <PanelBody className="divide-y divide-border-subtle p-0">
            {mattersQuery.isLoading ? <div className="p-4"><LoadingState label={common('loading')} /></div> : matters.length === 0 ? <p className="p-6 text-sm text-foreground-secondary">{t('noMatters')}</p> : matters.map((matter) => (
              <Link key={matter.id} href={localizedHref(locale, `/matters/${matter.id}`)} className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-surface-subtle">
                <span className="min-w-0 truncate font-medium">{matter.title}</span><StatusBadge status={matter.status === 'open' ? 'success' : 'neutral'} label={matter.status.toUpperCase()} />
              </Link>
            ))}
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader><h2 className="font-semibold">{t('upcomingDeadlines')}</h2><ViewAll locale={locale} href="/deadlines" label={t('viewAll')} /></PanelHeader>
          <PanelBody className="divide-y divide-border-subtle p-0">
            {deadlinesQuery.isLoading ? <div className="p-4"><LoadingState label={common('loading')} /></div> : deadlines.length === 0 ? <p className="p-6 text-sm text-foreground-secondary">{t('noDeadlines')}</p> : deadlines.map((deadline) => (
              <div key={deadline.id} className="flex items-center justify-between gap-4 px-4 py-3">
                <span className="min-w-0 truncate font-medium">{deadline.description}</span><time className="shrink-0 text-sm text-warning">{new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(deadline.due_date))}</time>
              </div>
            ))}
          </PanelBody>
        </Panel>

        <Panel className="xl:col-span-2">
          <PanelHeader><h2 className="font-semibold">{t('pendingReviews')}</h2><ViewAll locale={locale} href="/reviews" label={t('viewAll')} /></PanelHeader>
          <PanelBody className="divide-y divide-border-subtle p-0">
            {reviewsQuery.isLoading ? <div className="p-4"><LoadingState label={common('loading')} /></div> : reviews.length === 0 ? <p className="p-6 text-sm text-foreground-secondary">{t('noReviews')}</p> : reviews.map((review) => (
              <Link key={review.id} href={localizedHref(locale, `/reviews?review=${review.id}`)} className="grid gap-1 px-4 py-3 hover:bg-surface-subtle sm:grid-cols-[1fr_1fr_auto] sm:items-center">
                <span className="truncate font-medium">{review.entity_type}</span><span className="technical-id truncate text-foreground-muted">{review.entity_id}</span><StatusBadge status="review-required" label={review.status} />
              </Link>
            ))}
          </PanelBody>
        </Panel>
      </div>
    </div>
  )
}

function ViewAll({ locale, href, label }: { locale: AppLocale; href: string; label: string }) {
  return <Link href={localizedHref(locale, href)} className="inline-flex items-center gap-1 text-xs font-medium text-primary-content hover:underline">{label}<ArrowRight className="size-3.5" /></Link>
}
