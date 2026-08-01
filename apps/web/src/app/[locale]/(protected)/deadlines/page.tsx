'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { useQueryClient } from '@tanstack/react-query'
import { CalendarCheck2, CheckCircle2 } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { useMemo } from 'react'
import { toast } from 'react-hot-toast'

import { getListDeadlinesQueryKey, useCompleteDeadline, useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import type { DeadlineResponse } from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'
import { ApiError } from '@/lib/api/client'
import type { AppLocale } from '@/lib/navigation'

export default function DeadlinesPage() {
  const t = useTranslations('Deadlines')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const queryClient = useQueryClient()
  const deadlinesQuery = useListDeadlines()
  const completeDeadline = useCompleteDeadline()
  const deadlines = (deadlinesQuery.data ?? []).filter((deadline) => !deadline.is_completed)

  const columns = useMemo<ColumnDef<DeadlineResponse, unknown>[]>(() => [
    {
      accessorKey: 'description',
      header: ({ column }) => <SortableHeader label={t('descriptionColumn')} column={column} />,
      cell: ({ row }) => <span className="block max-w-[32rem] whitespace-normal font-medium">{row.original.description}</span>,
    },
    {
      accessorKey: 'matter_id',
      header: t('matter'),
      cell: ({ row }) => <span className="technical-id text-foreground-secondary">{row.original.matter_id.slice(0, 12)}</span>,
    },
    {
      accessorKey: 'due_date',
      header: ({ column }) => <SortableHeader label={t('dueDate')} column={column} />,
      cell: ({ row }) => {
        const dueDate = new Date(row.original.due_date)
        const overdue = dueDate < new Date()
        return <time dateTime={row.original.due_date} className={overdue ? 'font-medium text-danger' : 'text-foreground'}>{new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(dueDate)}</time>
      },
    },
    {
      id: 'timing',
      header: t('timing'),
      cell: ({ row }) => <StatusBadge status={new Date(row.original.due_date) < new Date() ? 'danger' : 'verified'} label={new Date(row.original.due_date) < new Date() ? t('overdue') : t('exact')} icon={CalendarCheck2} />,
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => (
        <Button
          variant="outline"
          size="sm"
          disabled={completeDeadline.isPending}
          onClick={() => completeDeadline.mutate({ deadlineId: row.original.id }, {
            onSuccess: () => {
              toast.success(t('completed'))
              queryClient.invalidateQueries({ queryKey: getListDeadlinesQueryKey() })
            },
            onError: (error: unknown) => toast.error(error instanceof ApiError ? error.message : t('completeError')),
          })}
        >
          <CheckCircle2 className="size-4" />{t('markComplete')}
        </Button>
      ),
    },
  ], [common, completeDeadline, locale, queryClient, t])

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      {deadlinesQuery.isLoading ? <LoadingState label={common('loading')} /> : deadlinesQuery.isError ? (
        <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => deadlinesQuery.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={deadlines}
          getRowId={(row) => row.id}
          copy={{
            search: t('descriptionColumn'),
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
