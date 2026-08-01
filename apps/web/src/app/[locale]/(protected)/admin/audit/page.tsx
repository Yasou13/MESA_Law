'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { useLocale, useTranslations } from 'next-intl'
import { useMemo } from 'react'

import { useListAuditEvents } from '@/api/endpoints/audit/audit'
import type { AuditEventResponse } from '@/api/models'
import { LoadingState } from '@/components/ui/async-state'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'
import type { AppLocale } from '@/lib/navigation'

function actionTone(action: string) {
  if (action.includes('DELETE') || action.includes('REMOVE')) return 'danger'
  if (action.includes('EXPORT') || action.includes('DOWNLOAD')) return 'warning'
  if (action.includes('RUN') || action.includes('AI')) return 'info'
  return 'success'
}

export default function AuditPage() {
  const t = useTranslations('Audit')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const { data: logs = [], isLoading } = useListAuditEvents()

  const columns = useMemo<ColumnDef<AuditEventResponse, unknown>[]>(() => [
    {
      accessorKey: 'user_id',
      header: ({ column }) => <SortableHeader label={t('principal')} column={column} />,
      cell: ({ row }) => <span className="technical-id block max-w-48 truncate">{row.original.user_id || t('system')}</span>,
    },
    {
      accessorKey: 'action',
      header: ({ column }) => <SortableHeader label={t('action')} column={column} />,
      cell: ({ row }) => <StatusBadge status={actionTone(row.original.action)} label={row.original.action.replaceAll('_', ' ')} />,
    },
    { accessorKey: 'entity_type', header: t('context'), cell: ({ row }) => <span className="uppercase text-foreground-secondary">{row.original.entity_type}</span> },
    { accessorKey: 'entity_id', header: t('resource'), cell: ({ row }) => <span className="technical-id block max-w-64 truncate">{row.original.entity_id}</span> },
    {
      accessorKey: 'timestamp',
      header: ({ column }) => <SortableHeader label={t('timestamp')} column={column} />,
      cell: ({ row }) => <time dateTime={row.original.timestamp}>{new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(row.original.timestamp))}</time>,
    },
    { id: 'state', header: () => null, cell: () => <span className="text-xs text-foreground-muted">{t('recorded')}</span> },
  ], [locale, t])

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {isLoading ? <LoadingState /> : (
        <DataTable
          columns={columns}
          data={logs}
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
