'use client'

import { ArrowRight, BriefcaseBusiness, MessageSquareText } from 'lucide-react'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'

import { useListMatters } from '@/api/endpoints/default/default'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel } from '@/components/ui/panel'
import { localizedHref } from '@/lib/navigation'

export default function AskMesaEntryPage() {
  const locale = useLocale() as 'tr' | 'en'
  const t = useTranslations('AskMesaEntry')
  const { data: matters = [], isLoading, isError, refetch } = useListMatters()

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        description={t('description')}
      />

      {isLoading ? (
        <LoadingState label={t('loading')} />
      ) : isError ? (
        <ErrorState
          title={t('loadError')}
          description={t('loadErrorDescription')}
          onRetry={() => refetch()}
        />
      ) : matters.length === 0 ? (
        <NoDataState
          title={t('emptyTitle')}
          description={t('emptyDescription')}
        />
      ) : (
        <Panel className="divide-y divide-border-subtle overflow-hidden">
          {matters.map((matter) => (
            <Link
              key={matter.id}
              href={localizedHref(locale, `/matters/${matter.id}/qa`)}
              className="group flex items-center gap-4 px-4 py-4 hover:bg-surface-subtle"
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-[var(--primary-soft)] text-primary">
                <BriefcaseBusiness className="size-4" aria-hidden="true" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold">{matter.title}</span>
                <span className="mt-0.5 block truncate text-xs text-foreground-secondary">
                  {matter.internal_reference ?? t('noReference')}
                </span>
              </span>
              <span className="hidden items-center gap-2 text-xs font-medium text-primary sm:flex">
                <MessageSquareText className="size-4" />
                {t('ask')}
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          ))}
        </Panel>
      )}
    </div>
  )
}
