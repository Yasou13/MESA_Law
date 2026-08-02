'use client'

import { AlertCircle, Bell, CheckCircle2, Info } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'

import { useListNotifications } from '@/api/endpoints/notifications/notifications'
import { LoadingState, NoDataState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel } from '@/components/ui/panel'
import type { AppLocale } from '@/lib/navigation'

function NotificationIcon({ category }: { category: string }) {
  const normalized = category.toLowerCase()
  if (normalized === 'error') return <span className="flex size-9 items-center justify-center rounded-full bg-danger-soft text-danger"><AlertCircle className="size-4" /></span>
  if (normalized === 'success') return <span className="flex size-9 items-center justify-center rounded-full bg-success-soft text-success"><CheckCircle2 className="size-4" /></span>
  return <span className="flex size-9 items-center justify-center rounded-full bg-info-soft text-info"><Info className="size-4" /></span>
}

export default function NotificationsPage() {
  const t = useTranslations('Notifications')
  const common = useTranslations('Common')
  const locale = useLocale() as AppLocale
  const { data: notifications = [], isLoading } = useListNotifications()

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {isLoading ? <LoadingState label={common('loading')} /> : notifications.length === 0 ? (
        <NoDataState title={t('emptyTitle')} description={t('emptyDescription')} />
      ) : (
        <Panel className="divide-y divide-border-subtle overflow-hidden">
          {notifications.map((notification) => (
            <article key={notification.id} className="flex gap-3 p-4 hover:bg-surface-subtle">
              <NotificationIcon category={notification.category} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                  <h2 className="truncate text-sm font-semibold">{notification.title}</h2>
                  <time className="shrink-0 text-xs text-foreground-muted" dateTime={notification.timestamp}>
                    {new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(notification.timestamp))}
                  </time>
                </div>
                <p className="mt-1 break-words text-sm leading-6 text-foreground-secondary">{notification.message}</p>
              </div>
            </article>
          ))}
        </Panel>
      )}
      <p className="flex items-center gap-2 text-xs text-foreground-muted"><Bell className="size-3.5" />{t('markAllUnavailable')}</p>
    </div>
  )
}
