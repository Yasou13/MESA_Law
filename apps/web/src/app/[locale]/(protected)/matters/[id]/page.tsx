'use client'

import { AlertTriangle, Database, FileCheck2, UsersRound } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { use, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

import {
  useGetMatter,
  useListClaims,
  useListMatterParties,
} from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import {
  getGetMesaBindingQueryKey,
  useCreateMesaBinding,
  useGetMesaBinding,
} from '@/api/endpoints/mesa-bindings/mesa-bindings'
import type { MesaBindingCreate, MesaBindingResponse } from '@/api/models'
import { LoadingState, NoDataState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Input } from '@/components/ui/input'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { StatusBadge } from '@/components/ui/status-badge'
import { ApiError } from '@/lib/api/client'

function readableError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.referenceId ? `${error.message} (${error.referenceId})` : error.message
  }
  return error instanceof Error ? error.message : fallback
}

type BindingField = keyof MesaBindingCreate

function bindingValue(form: MesaBindingCreate, field: BindingField): string {
  switch (field) {
    case 'mesa_tenant_id': return form.mesa_tenant_id
    case 'workspace_id': return form.workspace_id
    case 'dataset_id': return form.dataset_id
    case 'agent_id': return form.agent_id
  }
}

function updateBinding(form: MesaBindingCreate, field: BindingField, value: string): MesaBindingCreate {
  switch (field) {
    case 'mesa_tenant_id': return { ...form, mesa_tenant_id: value }
    case 'workspace_id': return { ...form, workspace_id: value }
    case 'dataset_id': return { ...form, dataset_id: value }
    case 'agent_id': return { ...form, agent_id: value }
  }
}

export default function MatterOverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const locale = useLocale() as 'tr' | 'en'
  const t = useTranslations('MatterOverview')
  const { data: matter } = useGetMatter(matterId)
  const { data: parties = [], isLoading: partiesLoading } = useListMatterParties(matterId)
  const { data: claims = [], isLoading: claimsLoading } = useListClaims(matterId)
  const { data: deadlines = [], isLoading: deadlinesLoading } = useListDeadlines({ matter_id: matterId })

  return (
    <div className="space-y-6">
      <MesaBindingCard matterId={matterId} canEdit={matter?.access_scope !== 'read'} />

      <div className="grid gap-6 xl:grid-cols-2">
        <OverviewPanel
          title={t('parties')}
          icon={UsersRound}
          loading={partiesLoading}
          empty={parties.length === 0}
          emptyText={t('partiesEmpty')}
          headers={[t('name'), t('role'), t('type')]}
          rows={parties.map((party) => [party.name, party.role, party.type])}
        />
        <OverviewPanel
          title={t('claims')}
          icon={FileCheck2}
          loading={claimsLoading}
          empty={claims.length === 0}
          emptyText={t('claimsEmpty')}
          headers={[t('description'), t('state'), t('review')]}
          rows={claims.map((claim) => [claim.description, claim.status, claim.review_status])}
        />
      </div>

      <OverviewPanel
        title={t('deadlines')}
        icon={AlertTriangle}
        loading={deadlinesLoading}
        empty={deadlines.length === 0}
        emptyText={t('deadlinesEmpty')}
        headers={[t('dueDate'), t('description'), t('state')]}
        rows={deadlines.map((deadline) => [
          new Intl.DateTimeFormat(locale).format(new Date(deadline.due_date)),
          deadline.description,
          deadline.is_completed ? t('completed') : t('open'),
        ])}
      />
    </div>
  )
}

function OverviewPanel({ title, icon: Icon, loading, empty, emptyText, headers, rows }: {
  title: string
  icon: typeof UsersRound
  loading: boolean
  empty: boolean
  emptyText: string
  headers: string[]
  rows: string[][]
}) {
  const [firstHeader, secondHeader, thirdHeader] = headers
  return (
    <Panel className="overflow-hidden">
      <PanelHeader>
        <h2 className="flex items-center gap-2 text-sm font-semibold"><Icon className="size-4 text-foreground-secondary" />{title}</h2>
      </PanelHeader>
      {loading ? (
        <PanelBody><LoadingState /></PanelBody>
      ) : empty ? (
        <PanelBody><NoDataState title={title} description={emptyText} /></PanelBody>
      ) : (
        <div className="divide-y divide-border-subtle">
          {rows.map(([firstCell, secondCell, thirdCell], rowIndex) => (
            <dl key={`${title}-${rowIndex}`} className="grid gap-2 px-4 py-3 sm:grid-cols-3">
              <div className="min-w-0"><dt className="text-[11px] font-medium text-foreground-muted">{firstHeader}</dt><dd className="mt-0.5 truncate text-sm">{firstCell}</dd></div>
              <div className="min-w-0"><dt className="text-[11px] font-medium text-foreground-muted">{secondHeader}</dt><dd className="mt-0.5 truncate text-sm">{secondCell}</dd></div>
              <div className="min-w-0"><dt className="text-[11px] font-medium text-foreground-muted">{thirdHeader}</dt><dd className="mt-0.5 truncate text-sm">{thirdCell}</dd></div>
            </dl>
          ))}
        </div>
      )}
    </Panel>
  )
}

function MesaBindingCard({ matterId, canEdit }: { matterId: string; canEdit: boolean }) {
  const t = useTranslations('MatterOverview')
  const common = useTranslations('Common')
  const queryClient = useQueryClient()
  const [form, setForm] = useState<MesaBindingCreate>({ mesa_tenant_id: '', workspace_id: '', dataset_id: '', agent_id: '' })
  const { data: binding, isLoading, error } = useGetMesaBinding<MesaBindingResponse, ApiError>(matterId, { query: { retry: false } })
  const createBinding = useCreateMesaBinding<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success(t('bindingSaved'))
        await queryClient.invalidateQueries({ queryKey: getGetMesaBindingQueryKey(matterId) })
      },
      onError: (mutationError) => toast.error(readableError(mutationError, t('bindingFailed'))),
    },
  })

  if (isLoading) return <Panel><PanelBody><LoadingState label={t('bindingLoading')} /></PanelBody></Panel>

  if (binding) {
    return (
      <Panel>
        <PanelHeader>
          <div><h2 className="text-sm font-semibold">MESA Core v4</h2><p className="mt-0.5 text-xs text-foreground-secondary">{t('bindingScope')}</p></div>
          <StatusBadge status={binding.provisioning_status === 'READY' ? 'verified' : binding.last_error ? 'danger' : 'processing'} label={binding.provisioning_status} />
        </PanelHeader>
        <PanelBody className="space-y-3">
          <dl className="grid gap-3 text-xs sm:grid-cols-3">
            <div><dt className="text-foreground-muted">Workspace</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.workspace_id}</dd></div>
            <div><dt className="text-foreground-muted">Dataset</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.dataset_id}</dd></div>
            <div><dt className="text-foreground-muted">Agent</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.agent_id}</dd></div>
          </dl>
          {binding.last_error && <InlineAlert tone="danger" title={t('preflightFailed')}>{binding.last_error}</InlineAlert>}
          <p className="text-xs text-foreground-secondary">{t('preflightNote')}</p>
        </PanelBody>
      </Panel>
    )
  }

  if (!(error instanceof ApiError && error.status === 404)) {
    return <InlineAlert tone="danger" title={t('bindingLoadError')}>{readableError(error, t('unknownError'))}</InlineAlert>
  }

  return (
    <Panel>
      <PanelHeader><div><h2 className="flex items-center gap-2 text-sm font-semibold"><Database className="size-4" />{t('bindTitle')}</h2><p className="mt-0.5 text-xs text-foreground-secondary">{t('bindDescription')}</p></div></PanelHeader>
      <PanelBody>
        <div className="grid gap-4 md:grid-cols-2">
          {(['mesa_tenant_id', 'workspace_id', 'dataset_id', 'agent_id'] as const).map((field) => (
            <label key={field} className="space-y-1.5 text-xs font-medium text-foreground-secondary">
              <span>{field}</span>
              <Input aria-label={field} value={bindingValue(form, field)} disabled={!canEdit || createBinding.isPending} onChange={(event) => setForm((current) => updateBinding(current, field, event.target.value))} />
            </label>
          ))}
        </div>
        <Button
          className="mt-4"
          aria-label={t('saveBindingLabel')}
          disabled={!canEdit || createBinding.isPending || Object.values(form).some((value) => !value.trim())}
          onClick={() => createBinding.mutate({ matterId, data: form })}
        >
          {createBinding.isPending ? common('saving') : t('saveBinding')}
        </Button>
      </PanelBody>
    </Panel>
  )
}
