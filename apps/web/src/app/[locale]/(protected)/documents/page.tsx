'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { Download, ExternalLink } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { useMemo } from 'react'
import { toast } from 'react-hot-toast'

import { downloadDocument, useListAllDocuments } from '@/api/endpoints/default/default'
import type { DocumentResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { Button, buttonVariants } from '@/components/ui/button'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { SourceBadge } from '@/components/ui/source-badge'
import { StatusBadge } from '@/components/ui/status-badge'
import { ApiError } from '@/lib/api/client'
import { localizedHref, type AppLocale } from '@/lib/navigation'

function documentTone(status: string) {
  if (['clean', 'ready', 'processed'].includes(status.toLowerCase())) return 'success' as const
  if (['failed', 'rejected', 'malicious'].includes(status.toLowerCase())) return 'error' as const
  return 'processing' as const
}

export default function GlobalDocumentsPage() {
  const t = useTranslations('Documents')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const { data: documents = [], isLoading, isError, refetch } = useListAllDocuments()

  const columns = useMemo<ColumnDef<DocumentResponse, unknown>[]>(() => [
    {
      accessorKey: 'title',
      header: ({ column }) => <SortableHeader label={t('name')} column={column} />,
      cell: ({ row }) => (
        <div className="min-w-0">
          <Link href={localizedHref(locale, `/documents/${row.original.id}`)} className="block max-w-[28rem] truncate font-medium text-primary hover:underline">
            {row.original.title}
          </Link>
          <span className="technical-id text-foreground-muted">{row.original.id.slice(0, 12)}</span>
        </div>
      ),
    },
    {
      accessorKey: 'matter_id',
      header: t('matter'),
      cell: ({ row }) => (
        <Link href={localizedHref(locale, `/matters/${row.original.matter_id}/documents`)} className="technical-id text-primary hover:underline">
          {row.original.matter_id.slice(0, 12)}
        </Link>
      ),
    },
    {
      accessorKey: 'status',
      header: ({ column }) => <SortableHeader label={common('status')} column={column} />,
      cell: ({ row }) => <StatusBadge status={documentTone(row.original.status)} label={row.original.status.toUpperCase()} />,
    },
    {
      accessorKey: 'provenance_state',
      header: t('provenance'),
      cell: ({ row }) => (
        <SourceBadge
          lowProvenance={row.original.provenance_state.toUpperCase() !== 'VERIFIED'}
          label={row.original.provenance_state.replaceAll('_', ' ')}
        />
      ),
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => <SortableHeader label={common('createdAt')} column={column} />,
      cell: ({ row }) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(row.original.created_at)),
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => (
        <div className="flex justify-end gap-1">
          <Link href={localizedHref(locale, `/documents/${row.original.id}`)} className={buttonVariants({ variant: 'ghost', size: 'icon-sm' })} aria-label={`${common('view')}: ${row.original.title}`}>
            <ExternalLink className="size-4" />
          </Link>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={`${common('download')}: ${row.original.title}`}
            onClick={async () => {
              try {
                const response = await downloadDocument(row.original.id)
                window.open(response.presigned_url, '_blank', 'noopener,noreferrer')
              } catch (error: unknown) {
                toast.error(error instanceof ApiError ? error.message : t('downloadError'))
              }
            }}
          >
            <Download className="size-4" />
          </Button>
        </div>
      ),
    },
  ], [common, locale, t])

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {isLoading ? <LoadingState label={common('loading')} /> : isError ? (
        <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={documents}
          getRowId={(row) => row.id}
          copy={{
            search: t('search'),
            emptyTitle: t('emptyTitle'),
            emptyDescription: t('emptyDescription'),
            previous: tableCopy('previous'),
            next: tableCopy('next'),
            page: (current, total) => tableCopy('page', { current, total }),
            rows: (visible, total) => tableCopy('rows', { visible, total }),
          }}
        />
      )}
    </div>
  )
}
