'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { UsersRound } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { use, useMemo } from 'react'

import { useListMatterParties } from '@/api/endpoints/default/default'
import type { MatterPartyResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'

export default function MatterPartiesPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const t = useTranslations('Parties')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const partiesQuery = useListMatterParties(matterId)
  const columns = useMemo<ColumnDef<MatterPartyResponse, unknown>[]>(() => [
    { accessorKey: 'name', header: ({ column }) => <SortableHeader label={t('name')} column={column} />, cell: ({ row }) => <span className="inline-flex max-w-80 items-center gap-2 truncate font-medium"><UsersRound className="size-4 shrink-0 text-foreground-muted" />{row.original.name}</span> },
    { accessorKey: 'role', header: ({ column }) => <SortableHeader label={t('role')} column={column} /> },
    { accessorKey: 'type', header: ({ column }) => <SortableHeader label={t('type')} column={column} /> },
    { accessorKey: 'id', header: 'ID', cell: ({ row }) => <span className="technical-id">{row.original.id.slice(0, 12)}</span> },
  ], [t])

  return <div className="space-y-6"><PageHeader title={t('title')} description={t('description')} />{partiesQuery.isLoading ? <LoadingState label={common('loading')} /> : partiesQuery.isError ? <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => partiesQuery.refetch()} /> : <DataTable columns={columns} data={partiesQuery.data ?? []} getRowId={(row) => row.id} copy={{ search: t('search'), emptyTitle: t('emptyTitle'), emptyDescription: t('emptyDescription'), previous: tableCopy('previous'), next: tableCopy('next'), page: (current, total) => tableCopy('page', { current, total }), rows: (visible, total) => tableCopy('rows', { visible, total }) }} />}</div>
}
