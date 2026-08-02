import { CalendarClock, FileText, Landmark, Scale, Upload, UserRound } from 'lucide-react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'

import { type MatterResponse } from '@/api/models'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'

export function MatterContextHeader({
  matter,
  uploadHref,
  nextDeadline,
  locale,
}: {
  matter: MatterResponse
  uploadHref: string
  nextDeadline?: string | null
  locale: 'tr' | 'en'
}) {
  const t = useTranslations('Shell')
  const isActive = ['open', 'active'].includes(matter.status.toLowerCase())

  return (
    <header className="space-y-4 border-b border-border bg-surface px-4 py-5 md:px-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-xl leading-7 font-semibold tracking-[-0.01em] text-foreground md:text-[28px] md:leading-9">
              {matter.title}
            </h1>
            <StatusBadge status={isActive ? 'success' : 'neutral'} label={matter.status} />
          </div>
          <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-foreground-secondary sm:text-sm">
            {matter.internal_reference && (
              <div className="flex items-center gap-1.5"><FileText className="size-4" /><dt className="sr-only">{t('reference')}</dt><dd className="tabular-nums">{matter.internal_reference}</dd></div>
            )}
            {matter.client_name && (
              <div className="flex items-center gap-1.5"><UserRound className="size-4" /><dt className="sr-only">{t('client')}</dt><dd>{matter.client_name}</dd></div>
            )}
            {matter.jurisdiction && (
              <div className="flex items-center gap-1.5"><Landmark className="size-4" /><dt className="sr-only">{t('jurisdiction')}</dt><dd>{matter.jurisdiction}</dd></div>
            )}
            {matter.case_type && (
              <div className="flex items-center gap-1.5"><Scale className="size-4" /><dt className="sr-only">{t('caseType')}</dt><dd>{matter.case_type}</dd></div>
            )}
            {nextDeadline && (
              <div className="flex items-center gap-1.5 text-warning"><CalendarClock className="size-4" /><dt className="sr-only">{t('nextDeadline')}</dt><dd>{nextDeadline}</dd></div>
            )}
          </dl>
        </div>
        {matter.access_scope !== 'read' && (
          <Button render={<Link href={uploadHref} />}>
            <Upload className="size-4" />{t('upload')}
          </Button>
        )}
      </div>

      <dl className="grid gap-2 text-xs text-foreground-secondary sm:grid-cols-2 lg:max-w-3xl lg:grid-cols-3">
        <div><dt className="font-medium text-foreground-muted">{t('confidentiality')}</dt><dd className="mt-0.5 text-foreground">{matter.confidentiality_level}</dd></div>
        <div><dt className="font-medium text-foreground-muted">{t('aiPolicy')}</dt><dd className="mt-0.5 text-foreground">{matter.ai_processing_policy}</dd></div>
        {matter.opened_at && <div><dt className="font-medium text-foreground-muted">{t('opened')}</dt><dd className="mt-0.5 text-foreground tabular-nums">{new Intl.DateTimeFormat(locale).format(new Date(matter.opened_at))}</dd></div>}
      </dl>
    </header>
  )
}
