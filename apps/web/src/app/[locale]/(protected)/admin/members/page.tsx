'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { Shield, UserRound } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useMemo } from 'react'

import { useListFirmMembers } from '@/api/endpoints/default/default'
import type { FirmMemberResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'

export default function MembersPage() {
  const t = useTranslations('Members')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const membersQuery = useListFirmMembers()

  const columns = useMemo<ColumnDef<FirmMemberResponse, unknown>[]>(() => [
    {
      accessorKey: 'full_name',
      header: ({ column }) => <SortableHeader label={t('user')} column={column} />,
      cell: ({ row }) => (
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface-subtle font-semibold text-primary-content" aria-hidden="true">
            {row.original.full_name?.charAt(0)?.toUpperCase() || <UserRound className="size-4" />}
          </div>
          <div className="min-w-0"><p className="truncate font-medium">{row.original.full_name || t('unnamed')}</p><p className="truncate text-xs text-foreground-muted">{row.original.email}</p></div>
        </div>
      ),
    },
    {
      accessorKey: 'role',
      header: ({ column }) => <SortableHeader label={t('role')} column={column} />,
      cell: ({ row }) => <span className="inline-flex items-center gap-2 capitalize"><Shield className="size-4 text-foreground-muted" />{row.original.role}</span>,
    },
    {
      accessorKey: 'is_active',
      header: common('status'),
      cell: ({ row }) => <StatusBadge status={row.original.is_active ? 'success' : 'danger'} label={row.original.is_active ? 'ACTIVE' : 'INACTIVE'} />,
    },
    {
      id: 'access',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: () => <span className="text-xs text-foreground-muted">{t('readOnly')}</span>,
    },
  ], [common, t])

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {membersQuery.isLoading ? <LoadingState label={common('loading')} /> : membersQuery.isError ? (
        <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => membersQuery.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={membersQuery.data ?? []}
          getRowId={(row) => row.id}
          copy={{
            search: t('search'), emptyTitle: t('emptyTitle'), emptyDescription: t('emptyDescription'),
            previous: tableCopy('previous'), next: tableCopy('next'),
            page: (current, total) => tableCopy('page', { current, total }),
            rows: (visible, total) => tableCopy('rows', { visible, total }),
          }}
        />
      )}
      <p className="text-xs text-foreground-muted">{t('inviteUnavailable')}</p>
    </div>
  )
}
