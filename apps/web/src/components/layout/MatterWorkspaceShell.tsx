'use client'

import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { useGetMatter } from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { MatterContextHeader } from '@/components/layout/MatterContextHeader'
import { cn } from '@/lib/utils'
import { localizedHref, pathnameWithoutLocale } from '@/lib/navigation'

const tabs = [
  { slug: '', key: 'overview' },
  { slug: 'timeline', key: 'timeline' },
  { slug: 'parties', key: 'parties' },
  { slug: 'documents', key: 'documents' },
  { slug: 'evidence', key: 'evidence' },
  { slug: 'research', key: 'research' },
  { slug: 'qa', key: 'qa' },
  { slug: 'reviews', key: 'reviews' },
  { slug: 'operations', key: 'operations' },
] as const

export function MatterWorkspaceShell({ matterId, children }: { matterId: string; children: React.ReactNode }) {
  const locale = useLocale() as 'tr' | 'en'
  const t = useTranslations('Shell')
  const navigationT = useTranslations('Navigation')
  const pathname = pathnameWithoutLocale(usePathname())
  const { data: matter, isLoading, isError, refetch } = useGetMatter(matterId)
  const { data: deadlines = [] } = useListDeadlines({ matter_id: matterId })
  const nextDeadline = deadlines
    .filter((item) => !item.is_completed && new Date(item.due_date).getTime() >= Date.now())
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0]

  if (isLoading) return <LoadingState label={t('matterLoading')} />
  if (isError || !matter) {
    return (
      <ErrorState
        title={t('matterLoadError')}
        description={t('matterLoadErrorDescription')}
        onRetry={() => refetch()}
      />
    )
  }

  const base = `/matters/${matterId}`
  return (
    <div className="-m-4 min-h-[calc(100vh-4rem)] border-x border-border bg-background md:-m-6 lg:-m-8">
      <MatterContextHeader
        matter={matter}
        locale={locale}
        uploadHref={localizedHref(locale, `${base}/documents?upload=1`)}
        nextDeadline={nextDeadline
          ? `${new Intl.DateTimeFormat(locale).format(new Date(nextDeadline.due_date))} · ${nextDeadline.description}`
          : null}
      />
      <nav data-testid="matter-tabs" className="overflow-x-auto border-b border-border bg-surface px-3 md:px-5" aria-label={t('matterSections')}>
        <div className="flex min-w-max gap-1">
          {tabs.map((tab) => {
            const href = tab.slug ? `${base}/${tab.slug}` : base
            const active = tab.slug ? pathname === href : pathname === base
            return (
              <Link
                key={tab.slug || 'overview'}
                href={localizedHref(locale, href)}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'relative flex h-11 items-center px-3 text-[13px] font-medium text-foreground-secondary hover:text-foreground',
                  active && 'text-primary-content after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-primary',
                )}
              >
                {tab.key === 'qa' ? navigationT('askMesa') : t(tab.key)}
              </Link>
            )
          })}
        </div>
      </nav>
      <div className="p-4 md:p-6 lg:p-8">{children}</div>
    </div>
  )
}
