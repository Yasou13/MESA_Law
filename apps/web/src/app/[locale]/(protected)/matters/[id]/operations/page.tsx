'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { useLocale, useTranslations } from 'next-intl'
import { use, useMemo } from 'react'

import { useListJobs } from '@/api/endpoints/operations/operations'
import type { JobResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'
import type { AppLocale } from '@/lib/navigation'

export default function MatterOperationsPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const t = useTranslations('Operations')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const jobsQuery = useListJobs({ limit: 100 })
  const jobs = (jobsQuery.data ?? []).filter((job) => job.matter_id === matterId)
  const columns = useMemo<ColumnDef<JobResponse, unknown>[]>(() => [
    { accessorKey: 'type', header: ({ column }) => <SortableHeader label={t('job')} column={column} />, cell: ({ row }) => <span className="font-medium">{row.original.type.replaceAll('_', ' ')}</span> },
    { accessorKey: 'status', header: ({ column }) => <SortableHeader label={common('status')} column={column} />, cell: ({ row }) => <StatusBadge status={row.original.status} label={row.original.status} /> },
    { accessorKey: 'retries', header: t('attempt'), cell: ({ row }) => `${row.original.retries + 1} / ${row.original.max_retries}` },
    { accessorKey: 'updated_at', header: ({ column }) => <SortableHeader label={common('updatedAt')} column={column} />, cell: ({ row }) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(row.original.updated_at)) },
    { accessorKey: 'id', header: 'Correlation ID', cell: ({ row }) => <span className="technical-id">{row.original.id.slice(0, 12)}</span> },
  ], [common, locale, t])
  return <div className="space-y-6"><PageHeader title={t('matterTitle')} description={t('matterDescription')} />{jobsQuery.isLoading ? <LoadingState label={common('loading')} /> : jobsQuery.isError ? <ErrorState title={t('matterLoadError')} description={t('matterLoadErrorDescription')} onRetry={() => jobsQuery.refetch()} /> : <DataTable columns={columns} data={jobs} getRowId={(row) => row.id} copy={{ search: t('search'), emptyTitle: t('emptyTitle'), emptyDescription: t('matterEmptyDescription'), previous: tableCopy('previous'), next: tableCopy('next'), page: (current, total) => tableCopy('page', { current, total }), rows: (visible, total) => tableCopy('rows', { visible, total }) }} />}</div>
}
