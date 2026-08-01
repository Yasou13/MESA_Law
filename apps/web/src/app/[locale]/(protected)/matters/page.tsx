'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import type { ColumnDef } from '@tanstack/react-table'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Loader2, Plus } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { z } from 'zod'

import {
  getListMattersQueryKey,
  useConflictCheck,
  useCreateMatter,
  useListMatters,
  useOverrideConflict,
} from '@/api/endpoints/default/default'
import type { ConflictResult, MatterResponse } from '@/api/models'
import { LoadingState } from '@/components/ui/async-state'
import { Button, buttonVariants } from '@/components/ui/button'
import { DataTable, SortableHeader } from '@/components/ui/data-table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/ui/page-header'
import { StatusBadge } from '@/components/ui/status-badge'
import { cn } from '@/lib/utils'
import { localizedHref, type AppLocale } from '@/lib/navigation'

const matterSchema = z.object({
  title: z.string().trim().min(3),
  partyNames: z.string().trim().min(1),
})

type MatterFormValues = z.infer<typeof matterSchema>
type StatusFilter = 'all' | 'active' | 'pending' | 'closed'

function statusTone(status: string) {
  const normalized = status.toLowerCase()
  if (normalized === 'open' || normalized === 'active') return 'success' as const
  if (normalized === 'pending') return 'review-required' as const
  return 'neutral' as const
}

export default function MattersPage() {
  const t = useTranslations('Matters')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [conflicts, setConflicts] = useState<ConflictResult[] | null>(null)
  const [overrideReason, setOverrideReason] = useState('')

  const { data: allMatters = [], isLoading } = useListMatters()
  const conflictCheck = useConflictCheck()
  const createMatter = useCreateMatter()
  const overrideConflict = useOverrideConflict()
  const { register, handleSubmit, reset, formState: { errors } } = useForm<MatterFormValues>({
    resolver: zodResolver(matterSchema),
    defaultValues: { title: '', partyNames: '' },
  })

  const filteredMatters = useMemo(() => allMatters.filter((matter) => {
    const status = matter.status.toLowerCase()
    if (statusFilter === 'active') return status === 'open' || status === 'active'
    if (statusFilter === 'pending') return status === 'pending'
    if (statusFilter === 'closed') return status === 'closed'
    return true
  }), [allMatters, statusFilter])

  const columns = useMemo<ColumnDef<MatterResponse, unknown>[]>(() => [
    {
      accessorKey: 'title',
      header: ({ column }) => <SortableHeader label={t('name')} column={column} />,
      cell: ({ row }) => (
        <div className="min-w-0">
          <Link href={localizedHref(locale, `/matters/${row.original.id}`)} className="block max-w-[24rem] truncate font-medium text-primary-content hover:underline">
            {row.original.title}
          </Link>
          <span className="technical-id text-foreground-muted">{row.original.id.slice(0, 12)}</span>
        </div>
      ),
    },
    {
      accessorKey: 'client_name',
      header: t('client'),
      cell: ({ row }) => <span className="block max-w-52 truncate">{row.original.client_name ?? common('notAvailable')}</span>,
    },
    {
      accessorKey: 'responsible_attorney',
      header: t('attorney'),
      cell: ({ row }) => <span className="block max-w-52 truncate">{row.original.responsible_attorney ?? common('notAvailable')}</span>,
    },
    {
      accessorKey: 'status',
      header: ({ column }) => <SortableHeader label={common('status')} column={column} />,
      cell: ({ row }) => <StatusBadge status={statusTone(row.original.status)} label={row.original.status.toUpperCase()} />,
    },
    {
      accessorKey: 'updated_at',
      header: ({ column }) => <SortableHeader label={common('updatedAt')} column={column} />,
      cell: ({ row }) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(row.original.updated_at)),
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => (
        <Link href={localizedHref(locale, `/matters/${row.original.id}`)} className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
          {common('open')}<ArrowRight className="size-4" />
        </Link>
      ),
    },
  ], [common, locale, t])

  const finishCreation = () => {
    queryClient.invalidateQueries({ queryKey: getListMattersQueryKey() })
    reset()
    setIsCreateOpen(false)
    setConflicts(null)
    setOverrideReason('')
  }

  const createWorkspace = async (data: MatterFormValues, reason?: string) => {
    let createdMatter: MatterResponse | undefined
    try {
      createdMatter = await createMatter.mutateAsync({ data: { title: data.title } })
      if (reason) await overrideConflict.mutateAsync({ matterId: createdMatter.id, data: { reason } })
      finishCreation()
      toast.success(reason ? t('createdOverride') : t('created'))
    } catch {
      if (createdMatter) {
        finishCreation()
        toast.error(t('overrideError'))
      } else {
        toast.error(t('createError'))
      }
    }
  }

  const onSubmit = async (data: MatterFormValues) => {
    if (conflicts !== null) {
      const reason = overrideReason.trim()
      if (reason.length < 3) {
        toast.error(t('overrideReasonError'))
        return
      }
      await createWorkspace(data, reason)
      return
    }
    const parties = data.partyNames.split(',').map((party) => party.trim()).filter(Boolean)
    conflictCheck.mutate({ data: { party_names: parties } }, {
      onSuccess: (result) => result.has_conflicts ? setConflicts(result.conflicts) : void createWorkspace(data),
      onError: () => toast.error(t('conflictCheckError')),
    })
  }

  const mutationPending = createMatter.isPending || conflictCheck.isPending || overrideConflict.isPending

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        description={t('description')}
        actions={
          <Dialog open={isCreateOpen} onOpenChange={(open) => { setIsCreateOpen(open); if (!open) setConflicts(null) }}>
            <DialogTrigger render={<Button />}><Plus className="size-4" />{t('new')}</DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <form onSubmit={handleSubmit(onSubmit)}>
                <DialogHeader>
                  <DialogTitle>{t('createTitle')}</DialogTitle>
                  <DialogDescription>{t('createDescription')}</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-5">
                  {conflicts === null ? (
                    <>
                      <div className="space-y-2">
                        <label htmlFor="title" className="text-sm font-medium">{t('name')}</label>
                        <Input id="title" placeholder={t('namePlaceholder')} {...register('title')} aria-invalid={Boolean(errors.title)} />
                        {errors.title && <p className="text-sm text-danger">{t('nameValidation')}</p>}
                      </div>
                      <div className="space-y-2">
                        <label htmlFor="partyNames" className="text-sm font-medium">{t('parties')}</label>
                        <Input id="partyNames" placeholder={t('partiesPlaceholder')} {...register('partyNames')} aria-invalid={Boolean(errors.partyNames)} />
                        {errors.partyNames && <p className="text-sm text-danger">{t('partiesValidation')}</p>}
                      </div>
                    </>
                  ) : (
                    <div className="space-y-4">
                      <div className="rounded-md border border-danger/30 bg-danger-soft p-4 text-sm">
                        <h3 className="font-semibold text-danger">{t('conflictTitle')}</h3>
                        <p className="mt-1 text-foreground-secondary">{t('conflictDescription')}</p>
                        <ul className="mt-3 space-y-2">
                          {conflicts.map((conflict, index) => (
                            <li key={`${conflict.matter_id}-${index}`} className="rounded border border-border bg-surface p-2">
                              <span className="font-medium">{conflict.matched_name}</span> · {conflict.matter_title} · {conflict.role}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="space-y-2">
                        <label htmlFor="overrideReason" className="text-sm font-medium">{t('overrideReason')}</label>
                        <Input id="overrideReason" value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} placeholder={t('overridePlaceholder')} minLength={3} required />
                        <p className="text-xs text-foreground-muted">{t('overrideAudit')}</p>
                      </div>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => conflicts ? (setConflicts(null), setOverrideReason('')) : setIsCreateOpen(false)}>
                    {conflicts ? common('back') : common('cancel')}
                  </Button>
                  <Button type="submit" disabled={mutationPending}>
                    {mutationPending && <Loader2 className="size-4 animate-spin" />}
                    {conflicts ? t('overrideCreate') : t('checkCreate')}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex flex-wrap gap-2" aria-label={common('status')}>
        {(['all', 'active', 'pending', 'closed'] as const).map((filter) => (
          <Button key={filter} size="sm" variant={statusFilter === filter ? 'default' : 'outline'} onClick={() => setStatusFilter(filter)} className={cn('capitalize')}>
            {filter === 'all' ? `${t('title')} (${allMatters.length})` : `${filter} (${allMatters.filter((matter) => filter === 'active' ? ['open', 'active'].includes(matter.status.toLowerCase()) : matter.status.toLowerCase() === filter).length})`}
          </Button>
        ))}
      </div>

      {isLoading ? <LoadingState label={common('loading')} /> : (
        <DataTable
          columns={columns}
          data={filteredMatters}
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
