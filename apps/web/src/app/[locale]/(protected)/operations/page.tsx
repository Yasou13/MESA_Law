'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { AlertCircle, CheckCircle2, Clock3, FileStack, Layers3, RefreshCw, RotateCw, ServerCog } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { useMemo, useState } from 'react'

import { useListJobs } from '@/api/endpoints/operations/operations'
import type { JobResponse } from '@/api/models'
import { LoadingState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { PageHeader } from '@/components/ui/page-header'
import { Panel, PanelBody } from '@/components/ui/panel'
import { StatusBadge } from '@/components/ui/status-badge'
import type { AppLocale } from '@/lib/navigation'

type OperationGroup = 'all' | 'document' | 'scope' | 'mesa' | 'failed'

function operationGroup(job: JobResponse): Exclude<OperationGroup, 'all' | 'failed'> {
  const type = job.type.toLowerCase()
  if (type.includes('mesa') || type.includes('publish') || type.includes('mutation')) return 'mesa'
  if (type.includes('scope') || type.includes('binding') || type.includes('session')) return 'scope'
  return 'document'
}

function jobTone(status: string) {
  if (status === 'SUCCEEDED') return 'success'
  if (status === 'FAILED' || status === 'DEAD') return 'error'
  if (status === 'RUNNING') return 'processing'
  return 'neutral'
}

export default function OperationsPage() {
  const t = useTranslations('Operations')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const [group, setGroup] = useState<OperationGroup>('all')
  const [selectedJob, setSelectedJob] = useState<JobResponse | null>(null)
  const { data: jobs = [], isLoading, refetch } = useListJobs()

  const groupedJobs = useMemo(() => jobs.filter((job) => {
    if (group === 'all') return true
    if (group === 'failed') return ['FAILED', 'DEAD'].includes(job.status) || job.retries > 0
    return operationGroup(job) === group
  }), [group, jobs])

  const columns = useMemo<ColumnDef<JobResponse, unknown>[]>(() => [
    {
      accessorKey: 'type',
      header: ({ column }) => <SortableHeader label={t('job')} column={column} />,
      cell: ({ row }) => (
        <div className="min-w-0">
          <p className="max-w-72 truncate font-medium">{row.original.type.replaceAll('_', ' ')}</p>
          <p className="technical-id max-w-72 truncate text-foreground-muted">{row.original.id}</p>
        </div>
      ),
    },
    {
      accessorKey: 'matter_id',
      header: t('matter'),
      cell: ({ row }) => <span className="technical-id text-foreground-secondary">{row.original.matter_id?.slice(0, 12) ?? common('notAvailable')}</span>,
    },
    {
      accessorKey: 'status',
      header: ({ column }) => <SortableHeader label={common('status')} column={column} />,
      cell: ({ row }) => <StatusBadge status={jobTone(row.original.status)} label={row.original.status} />,
    },
    {
      accessorKey: 'retries',
      header: t('attempt'),
      cell: ({ row }) => <span>{row.original.retries + 1} / {row.original.max_retries}</span>,
    },
    {
      accessorKey: 'updated_at',
      header: ({ column }) => <SortableHeader label={common('updatedAt')} column={column} />,
      cell: ({ row }) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(row.original.updated_at)),
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => (
        <Button variant="ghost" size="sm" onClick={() => setSelectedJob(row.original)}>
          {t('details')}
        </Button>
      ),
    },
  ], [common, locale, t])

  const metrics = [
    { label: t('returned'), value: jobs.length, icon: ServerCog, tone: 'text-info' },
    { label: t('processing'), value: jobs.filter((job) => job.status === 'RUNNING').length, icon: RotateCw, tone: 'text-info' },
    { label: t('completed'), value: jobs.filter((job) => job.status === 'SUCCEEDED').length, icon: CheckCircle2, tone: 'text-success' },
    { label: t('failed'), value: jobs.filter((job) => ['FAILED', 'DEAD'].includes(job.status)).length, icon: AlertCircle, tone: 'text-danger' },
  ]

  const getGroupIcon = (item: OperationGroup) => {
    if (item === 'document') return FileStack
    if (item === 'scope') return Clock3
    if (item === 'mesa') return ServerCog
    if (item === 'failed') return AlertCircle
    return Layers3
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        description={t('description')}
        actions={<Button variant="outline" onClick={() => refetch()} disabled={isLoading}><RefreshCw className={isLoading ? 'animate-spin' : ''} />{common('refresh')}</Button>}
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Panel key={metric.label}>
            <PanelBody className="flex items-center justify-between">
              <div><p className="text-xs font-medium text-foreground-secondary">{metric.label}</p><p className="mt-1 text-2xl font-semibold tabular-nums">{metric.value}</p></div>
              <metric.icon className={`size-5 ${metric.tone}`} aria-hidden="true" />
            </PanelBody>
          </Panel>
        ))}
      </div>

      <div className="flex max-w-full gap-2 overflow-x-auto pb-1" aria-label={common('status')}>
        {(['all', 'document', 'scope', 'mesa', 'failed'] as const).map((item) => {
          const Icon = getGroupIcon(item)
          return <Button key={item} variant={group === item ? 'default' : 'outline'} size="sm" onClick={() => setGroup(item)}><Icon className="size-4" />{t(`groups.${item}`)}</Button>
        })}
      </div>

      {isLoading ? <LoadingState label={common('loading')} /> : (
        <DataTable
          columns={columns}
          data={groupedJobs}
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

      <Dialog open={Boolean(selectedJob)} onOpenChange={(open) => !open && setSelectedJob(null)}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{t('technicalDetail')}</DialogTitle>
            <DialogDescription className="technical-id break-all">{selectedJob?.id}</DialogDescription>
          </DialogHeader>
          {selectedJob && (
            <dl className="grid gap-3 text-sm sm:grid-cols-[9rem_1fr]">
              <dt className="text-foreground-secondary">{t('job')}</dt><dd className="break-all">{selectedJob.type}</dd>
              <dt className="text-foreground-secondary">{common('status')}</dt><dd><StatusBadge status={jobTone(selectedJob.status)} label={selectedJob.status} /></dd>
              <dt className="text-foreground-secondary">{t('matter')}</dt><dd className="technical-id break-all">{selectedJob.matter_id ?? common('notAvailable')}</dd>
              <dt className="text-foreground-secondary">{t('attempt')}</dt><dd>{selectedJob.retries + 1} / {selectedJob.max_retries}</dd>
              <dt className="text-foreground-secondary">{t('payload')}</dt><dd><pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-md bg-surface-subtle p-3 text-xs">{JSON.stringify(selectedJob.payload, null, 2)}</pre></dd>
              {selectedJob.error_message && <><dt className="text-danger">{t('error')}</dt><dd className="break-words rounded-md bg-danger-soft p-3 text-danger">{selectedJob.error_message}</dd></>}
            </dl>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
