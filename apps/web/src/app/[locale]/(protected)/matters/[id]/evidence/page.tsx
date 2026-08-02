'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { ExternalLink } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { use, useMemo } from 'react'

import { useListEvidence } from '@/api/endpoints/default/default'
import type { EvidenceResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { buttonVariants } from '@/components/ui/button'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'
import { localizedHref, type AppLocale } from '@/lib/navigation'

export default function MatterEvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: matterId } = use(params)
  const t = useTranslations('Evidence')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const evidenceQuery = useListEvidence(matterId)
  const evidence = Array.isArray(evidenceQuery.data) ? evidenceQuery.data : []

  const columns = useMemo<ColumnDef<EvidenceResponse, unknown>[]>(() => [
    {
      accessorKey: 'description',
      header: ({ column }) => <SortableHeader label={t('content')} column={column} />,
      cell: ({ row }) => <blockquote className="evidence-text max-w-[34rem] whitespace-normal text-sm leading-6">{row.original.description}</blockquote>,
    },
    {
      accessorKey: 'document_id',
      header: t('source'),
      cell: ({ row }) => row.original.document_id ? (
        <Link href={localizedHref(locale, `/documents/${row.original.document_id}`)} className="technical-id text-primary-content hover:underline">{row.original.document_id.slice(0, 12)}</Link>
      ) : <span className="text-foreground-muted">{common('notAvailable')}</span>,
    },
    {
      accessorKey: 'review_status',
      header: ({ column }) => <SortableHeader label={common('status')} column={column} />,
      cell: ({ row }) => <StatusBadge status={row.original.review_status === 'APPROVED' ? 'success' : row.original.review_status === 'REJECTED' ? 'danger' : 'review-required'} label={row.original.review_status} />,
    },
    {
      accessorKey: 'source_locator_id',
      header: t('locator'),
      cell: ({ row }) => <span className="technical-id text-foreground-muted">{row.original.source_locator_id?.slice(0, 12) ?? t('pendingLocator')}</span>,
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => row.original.document_id ? (
        <Link href={localizedHref(locale, `/documents/${row.original.document_id}`)} className={buttonVariants({ variant: 'ghost', size: 'sm' })}>{t('openSource')}<ExternalLink className="size-4" /></Link>
      ) : null,
    },
  ], [common, locale, t])

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {evidenceQuery.isLoading ? <LoadingState label={common('loading')} /> : evidenceQuery.isError ? (
        <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => evidenceQuery.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={evidence}
          getRowId={(row) => row.id}
          copy={{
            search: t('search'), emptyTitle: t('emptyTitle'), emptyDescription: t('emptyDescription'),
            previous: tableCopy('previous'), next: tableCopy('next'),
            page: (current, total) => tableCopy('page', { current, total }),
            rows: (visible, total) => tableCopy('rows', { visible, total }),
          }}
        />
      )}
    </div>
  )
}
