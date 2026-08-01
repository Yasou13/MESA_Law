'use client'

import { ArrowRight, BriefcaseBusiness, MessageSquareText } from 'lucide-react'
import Link from 'next/link'
import { useLocale } from 'next-intl'

import { useListMatters } from '@/api/endpoints/default/default'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel } from '@/components/ui/panel'
import { localizedHref } from '@/lib/navigation'

export default function AskMesaEntryPage() {
  const locale = useLocale() as 'tr' | 'en'
  const { data: matters = [], isLoading, isError, refetch } = useListMatters()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ask MESA"
        description={locale === 'tr'
          ? 'Kaynaklı soru-cevap yalnızca seçtiğiniz dosyanın doğrulanmış belge kapsamı içinde çalışır.'
          : 'Sourced Q&A only works within the verified document scope of the matter you select.'}
      />

      {isLoading ? (
        <LoadingState label={locale === 'tr' ? 'Dosyalar yükleniyor' : 'Loading matters'} />
      ) : isError ? (
        <ErrorState
          title={locale === 'tr' ? 'Dosyalar yüklenemedi' : 'Matters could not be loaded'}
          description={locale === 'tr' ? 'Verileriniz korunuyor. Yeniden deneyebilirsiniz.' : 'Your data remains safe. You can try again.'}
          onRetry={() => refetch()}
        />
      ) : matters.length === 0 ? (
        <NoDataState
          title={locale === 'tr' ? 'Soru sorulacak dosya bulunmuyor' : 'No matter is available for Q&A'}
          description={locale === 'tr' ? 'Önce erişiminiz olan bir dosya oluşturun.' : 'Create a matter you can access first.'}
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
                  {matter.internal_reference ?? (locale === 'tr' ? 'Dosya numarası belirtilmedi' : 'No matter reference')}
                </span>
              </span>
              <span className="hidden items-center gap-2 text-xs font-medium text-primary sm:flex">
                <MessageSquareText className="size-4" />
                {locale === 'tr' ? 'Dosyada sor' : 'Ask in matter'}
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          ))}
        </Panel>
      )}
    </div>
  )
}
