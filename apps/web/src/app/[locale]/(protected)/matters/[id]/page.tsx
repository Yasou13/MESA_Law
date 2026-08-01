'use client'

import { AlertTriangle, Database, FileCheck2, UsersRound } from 'lucide-react'
import { useLocale } from 'next-intl'
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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
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
  const { data: matter } = useGetMatter(matterId)
  const { data: parties = [], isLoading: partiesLoading } = useListMatterParties(matterId)
  const { data: claims = [], isLoading: claimsLoading } = useListClaims(matterId)
  const { data: deadlines = [], isLoading: deadlinesLoading } = useListDeadlines({ matter_id: matterId })

  return (
    <div className="space-y-6">
      <MesaBindingCard matterId={matterId} canEdit={matter?.access_scope !== 'read'} locale={locale} />

      <div className="grid gap-6 xl:grid-cols-2">
        <OverviewPanel
          title={locale === 'tr' ? 'Taraflar' : 'Parties'}
          icon={UsersRound}
          loading={partiesLoading}
          empty={parties.length === 0}
          emptyText={locale === 'tr' ? 'Bu dosyada henüz taraf kaydı bulunmuyor.' : 'No parties are recorded for this matter.'}
          headers={locale === 'tr' ? ['Ad', 'Rol', 'Tür'] : ['Name', 'Role', 'Type']}
          rows={parties.map((party) => [party.name, party.role, party.type])}
        />
        <OverviewPanel
          title={locale === 'tr' ? 'Canonical iddialar' : 'Canonical claims'}
          icon={FileCheck2}
          loading={claimsLoading}
          empty={claims.length === 0}
          emptyText={locale === 'tr' ? 'İncelenmiş canonical iddia bulunmuyor.' : 'No reviewed canonical claim is available.'}
          headers={locale === 'tr' ? ['Açıklama', 'Durum', 'İnceleme'] : ['Description', 'Status', 'Review']}
          rows={claims.map((claim) => [claim.description, claim.status, claim.review_status])}
        />
      </div>

      <OverviewPanel
        title={locale === 'tr' ? 'Manuel süreler' : 'Manual deadlines'}
        icon={AlertTriangle}
        loading={deadlinesLoading}
        empty={deadlines.length === 0}
        emptyText={locale === 'tr' ? 'Bu dosyada manuel süre kaydı bulunmuyor.' : 'No manual deadline is recorded for this matter.'}
        headers={locale === 'tr' ? ['Son tarih', 'Açıklama', 'Durum'] : ['Due date', 'Description', 'State']}
        rows={deadlines.map((deadline) => [
          new Intl.DateTimeFormat(locale === 'tr' ? 'tr-TR' : 'en-GB').format(new Date(deadline.due_date)),
          deadline.description,
          deadline.is_completed ? (locale === 'tr' ? 'Tamamlandı' : 'Completed') : (locale === 'tr' ? 'Açık' : 'Open'),
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
        <Table>
          <TableHeader><TableRow>{headers.map((header) => <TableHead key={header}>{header}</TableHead>)}</TableRow></TableHeader>
          <TableBody>{rows.map((row, rowIndex) => <TableRow key={`${title}-${rowIndex}`}>{row.map((cell, cellIndex) => <TableCell key={`${rowIndex}-${cellIndex}`}>{cell}</TableCell>)}</TableRow>)}</TableBody>
        </Table>
      )}
    </Panel>
  )
}

function MesaBindingCard({ matterId, canEdit, locale }: { matterId: string; canEdit: boolean; locale: 'tr' | 'en' }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<MesaBindingCreate>({ mesa_tenant_id: '', workspace_id: '', dataset_id: '', agent_id: '' })
  const { data: binding, isLoading, error } = useGetMesaBinding<MesaBindingResponse, ApiError>(matterId, { query: { retry: false } })
  const createBinding = useCreateMesaBinding<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success(locale === 'tr' ? 'MESA kapsamı kaydedildi; yetki kontrolü kuyruğa alındı' : 'Binding saved; MESA permission preflight queued')
        await queryClient.invalidateQueries({ queryKey: getGetMesaBindingQueryKey(matterId) })
      },
      onError: (mutationError) => toast.error(readableError(mutationError, locale === 'tr' ? 'MESA kapsamı kaydedilemedi' : 'Binding failed')),
    },
  })

  if (isLoading) return <Panel><PanelBody><LoadingState label={locale === 'tr' ? 'MESA kapsamı yükleniyor' : 'Loading MESA binding'} /></PanelBody></Panel>

  if (binding) {
    return (
      <Panel>
        <PanelHeader>
          <div><h2 className="text-sm font-semibold">MESA Core v4</h2><p className="mt-0.5 text-xs text-foreground-secondary">{locale === 'tr' ? 'Önceden hazırlanmış çalışma alanı kapsamı' : 'Pre-provisioned workspace scope'}</p></div>
          <StatusBadge status={binding.provisioning_status === 'READY' ? 'verified' : binding.last_error ? 'danger' : 'processing'} label={binding.provisioning_status} />
        </PanelHeader>
        <PanelBody className="space-y-3">
          <dl className="grid gap-3 text-xs sm:grid-cols-3">
            <div><dt className="text-foreground-muted">Workspace</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.workspace_id}</dd></div>
            <div><dt className="text-foreground-muted">Dataset</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.dataset_id}</dd></div>
            <div><dt className="text-foreground-muted">Agent</dt><dd className="technical-id mt-1 break-all text-foreground">{binding.agent_id}</dd></div>
          </dl>
          {binding.last_error && <InlineAlert tone="danger" title={locale === 'tr' ? 'MESA yetki kontrolü başarısız' : 'MESA preflight failed'}>{binding.last_error}</InlineAlert>}
          <p className="text-xs text-foreground-secondary">{locale === 'tr' ? 'Law yalnız preflight yapar; ACL hazırlığı harici mesa-v4-admin onboarding sorumluluğudur.' : 'Law performs preflight only; ACL provisioning remains an external mesa-v4-admin onboarding task.'}</p>
        </PanelBody>
      </Panel>
    )
  }

  if (!(error instanceof ApiError && error.status === 404)) {
    return <InlineAlert tone="danger" title={locale === 'tr' ? 'MESA kapsam durumu yüklenemedi' : 'MESA binding could not be loaded'}>{readableError(error, 'Unknown error')}</InlineAlert>
  }

  return (
    <Panel>
      <PanelHeader><div><h2 className="flex items-center gap-2 text-sm font-semibold"><Database className="size-4" />{locale === 'tr' ? 'MESA Core v4 kapsamını bağla' : 'Bind MESA Core v4 scope'}</h2><p className="mt-0.5 text-xs text-foreground-secondary">{locale === 'tr' ? 'Yalnız mesa-v4-admin tarafından önceden hazırlanmış kimlikleri girin.' : 'Enter identifiers already provisioned by mesa-v4-admin.'}</p></div></PanelHeader>
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
          aria-label="Save binding and run preflight"
          disabled={!canEdit || createBinding.isPending || Object.values(form).some((value) => !value.trim())}
          onClick={() => createBinding.mutate({ matterId, data: form })}
        >
          {createBinding.isPending ? (locale === 'tr' ? 'Kaydediliyor…' : 'Saving…') : (locale === 'tr' ? 'Kapsamı kaydet ve kontrol et' : 'Save binding and run preflight')}
        </Button>
      </PanelBody>
    </Panel>
  )
}
