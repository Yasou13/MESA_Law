'use client'

import { use, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, FileCheck, FileText, Loader2, UploadCloud } from 'lucide-react'
import { toast } from 'react-hot-toast'

import {
  downloadDocument,
  getListMatterDocumentsQueryKey,
  useCompleteUpload,
  useCreateUploadIntent,
  useGetMatter,
  useListClaims,
  useListMatterDocuments,
  useListMatterParties,
} from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import { useSaveDraft } from '@/api/endpoints/draft-studio/draft-studio'
import {
  getGetMesaBindingQueryKey,
  useCreateMesaBinding,
  useGetMesaBinding,
} from '@/api/endpoints/mesa-bindings/mesa-bindings'
import type { DocumentResponse, MesaBindingCreate, MesaBindingResponse } from '@/api/models'
import { MatterContextHeader } from '@/components/layout/MatterContextHeader'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'
import { DocumentViewer } from '@/features/documents/components/DocumentViewer'
import { DraftStudioShell } from '@/features/drafts/components/DraftStudioShell'
import { QAShell } from '@/features/qa/components/QAShell'
import { ResearchShell } from '@/features/research/components/ResearchShell'
import { ApiError } from '@/lib/api/client'

type MatterTab = 'overview' | 'documents' | 'qa' | 'drafts' | 'research'

function readableError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.referenceId ? `${error.message} (${error.referenceId})` : error.message
  }
  return error instanceof Error ? error.message : fallback
}

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const router = useRouter()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<MatterTab>('overview')
  const [activeDocument, setActiveDocument] = useState<{
    id: string
    url: string
    title: string
  } | null>(null)

  const { data: matter, isLoading: isLoadingMatter } = useGetMatter(matterId)
  const canEdit = matter?.access_scope !== 'read'
  const { data: documents = [], isLoading: isLoadingDocuments } = useListMatterDocuments(
    matterId,
    {
      query: {
        refetchInterval: (query) =>
          query.state.data?.some((document) =>
            ['UPLOADING', 'SCANNING', 'PROCESSING'].includes(document.status.toUpperCase()),
          )
            ? 3000
            : false,
      },
    },
  )
  const { data: claims = [], isLoading: isLoadingClaims } = useListClaims(matterId)
  const { data: parties = [], isLoading: isLoadingParties } = useListMatterParties(matterId)
  const { data: deadlines = [], isLoading: isLoadingDeadlines } = useListDeadlines({
    matter_id: matterId,
  })
  const uploadIntent = useCreateUploadIntent<ApiError>()
  const completeUpload = useCompleteUpload<ApiError>()
  const saveDraft = useSaveDraft<ApiError>()

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setIsUploading(true)
    setUploadProgress(0)
    try {
      const intent = await uploadIntent.mutateAsync({
        data: {
          matter_id: matterId,
          filename: file.name,
          mime_type: file.type || 'application/pdf',
          size_bytes: file.size,
        },
      })
      setUploadProgress(50)
      const uploadResponse = await fetch(intent.presigned_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type || 'application/pdf' },
      })
      if (!uploadResponse.ok) {
        throw new Error(`Object storage rejected the upload (${uploadResponse.status})`)
      }
      setUploadProgress(90)
      await completeUpload.mutateAsync({ documentId: intent.document_id })
      setUploadProgress(100)
      await queryClient.invalidateQueries({
        queryKey: getListMatterDocumentsQueryKey(matterId),
      })
      toast.success('Document uploaded and queued for security scanning')
    } catch (error: unknown) {
      toast.error(readableError(error, 'Upload failed'))
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const openDocument = async (document: DocumentResponse) => {
    try {
      const download = await downloadDocument(document.id)
      setActiveDocument({ id: document.id, title: document.title, url: download.presigned_url })
    } catch (error: unknown) {
      toast.error(readableError(error, 'Document is not available yet'))
    }
  }

  const handleCreateDraft = async () => {
    try {
      const draft = await saveDraft.mutateAsync({
        data: { matter_id: matterId, title: 'New Draft', content: '' },
      })
      toast.success('Draft created')
      router.push(`/drafts/${draft.id}`)
    } catch (error: unknown) {
      toast.error(readableError(error, 'Failed to create draft'))
    }
  }

  if (activeDocument) {
    return (
      <DocumentViewer
        documentId={activeDocument.id}
        matterId={matterId}
        url={activeDocument.url}
        title={activeDocument.title}
        onClose={() => setActiveDocument(null)}
      />
    )
  }

  return (
    <div className="flex h-full flex-col bg-[var(--background)]">
      {!isLoadingMatter && matter && (
        <MatterContextHeader
          matter={{
            name: matter.title,
            internal_reference: matter.internal_reference ?? matterId.slice(0, 8),
            client_name: matter.client_name ?? 'Not specified',
            responsible_attorney_name: 'Not assigned',
            status: matter.status,
            confidentiality_level: matter.confidentiality_level,
            legal_hold: false,
            ai_processing_policy: matter.ai_processing_policy,
          }}
        />
      )}

      <div className="border-b border-[var(--border-surface)] bg-[var(--bg-surface)] px-6 py-2">
        <div className="flex flex-wrap items-center gap-1">
          {(['overview', 'documents', 'qa', 'drafts', 'research'] as MatterTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[var(--bg-surface-hover)] text-[var(--foreground)]'
                  : 'text-[var(--color-anthracite-400)] hover:bg-[var(--bg-surface-hover)] hover:text-[var(--foreground)]'
              }`}
            >
              {tab === 'qa' ? 'Sourced Q&A' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
          <Link
            href={`/matters/${matterId}/reviews`}
            className="ml-auto inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium text-[var(--color-anthracite-400)] hover:bg-[var(--bg-surface-hover)] hover:text-[var(--foreground)]"
          >
            <FileCheck className="h-4 w-4" /> Reviews
          </Link>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6 md:p-8">
        <div className="mx-auto max-w-7xl">
          {activeTab === 'overview' && (
            <div className="space-y-8">
              <MesaBindingCard matterId={matterId} canEdit={canEdit} />
              <OverviewTable
                title="Matter parties"
                isLoading={isLoadingParties}
                isEmpty={parties.length === 0}
                headers={['Name', 'Role', 'Type']}
                rows={parties.map((party) => [party.name, party.role, party.type])}
              />
              <OverviewTable
                title="Canonical claims"
                isLoading={isLoadingClaims}
                isEmpty={claims.length === 0}
                headers={['Description', 'Status', 'Review status']}
                rows={claims.map((claim) => [claim.description, claim.status, claim.review_status])}
              />
              <OverviewTable
                title="Manual deadlines"
                isLoading={isLoadingDeadlines}
                isEmpty={deadlines.length === 0}
                headers={['Due date', 'Description', 'State']}
                rows={deadlines.map((deadline) => [
                  deadline.due_date,
                  deadline.description,
                  deadline.is_completed ? 'COMPLETED' : 'OPEN',
                ])}
              />
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-6">
              {canEdit && (
                <button
                  type="button"
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="w-full rounded-xl border-2 border-dashed border-[var(--border-surface)] bg-[var(--bg-surface)] p-6 text-center transition-colors hover:border-[var(--color-lila-500)] disabled:opacity-50"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={handleFileUpload}
                    accept=".pdf,.docx,.txt"
                  />
                  {isUploading ? (
                    <Loader2 className="mx-auto mb-2 h-8 w-8 animate-spin" />
                  ) : (
                    <UploadCloud className="mx-auto mb-2 h-8 w-8 text-[var(--color-anthracite-400)]" />
                  )}
                  <span className="text-sm font-medium text-[var(--foreground)]">
                    {isUploading ? `Uploading ${uploadProgress}%` : 'Upload PDF, DOCX or TXT'}
                  </span>
                </button>
              )}
              <div className="glass-card overflow-hidden rounded-xl border border-[var(--border-surface)]">
                <div className="border-b border-[var(--border-surface)] p-4 font-semibold">Matter documents</div>
                {isLoadingDocuments ? (
                  <div className="p-8 text-center">Loading…</div>
                ) : documents.length === 0 ? (
                  <div className="p-8 text-center text-[var(--color-anthracite-400)]">No documents uploaded.</div>
                ) : (
                  <div className="divide-y divide-[var(--border-surface)]">
                    {documents.map((document) => (
                      <button
                        type="button"
                        key={document.id}
                        onClick={() => openDocument(document)}
                        className="flex w-full items-center justify-between gap-4 p-4 text-left hover:bg-[var(--bg-surface-hover)]"
                      >
                        <div className="min-w-0">
                          <span className="flex items-center gap-2 truncate font-medium">
                            <FileText className="h-4 w-4 shrink-0" /> {document.title}
                          </span>
                          <span className="mt-1 block text-xs text-[var(--color-anthracite-400)]">
                            {document.provenance_state}
                            {document.failure_reason ? ` · ${document.failure_reason}` : ''}
                          </span>
                        </div>
                        <StatusBadge status="neutral" label={document.status} />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'qa' && <QAShell matterId={matterId} />}
          {activeTab === 'drafts' && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <Button onClick={handleCreateDraft} disabled={saveDraft.isPending}>
                  {saveDraft.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  New manual draft
                </Button>
              </div>
              <DraftStudioShell matterId={matterId} />
            </div>
          )}
          {activeTab === 'research' && <ResearchShell matterId={matterId} />}
        </div>
      </div>
    </div>
  )
}

function OverviewTable({
  title,
  isLoading,
  isEmpty,
  headers,
  rows,
}: {
  title: string
  isLoading: boolean
  isEmpty: boolean
  headers: string[]
  rows: string[][]
}) {
  return (
    <section className="glass-card overflow-hidden rounded-xl border border-[var(--border-surface)]">
      <h3 className="border-b border-[var(--border-surface)] bg-[var(--bg-surface)] p-4 font-semibold">
        {title}
      </h3>
      <div className="overflow-x-auto p-4">
        {isLoading ? (
          <p className="py-4 text-center text-sm">Loading…</p>
        ) : isEmpty ? (
          <p className="py-4 text-center text-sm text-[var(--color-anthracite-400)]">No records.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--bg-surface-hover)] text-xs uppercase text-[var(--color-anthracite-400)]">
              <tr>{headers.map((header) => <th key={header} className="px-4 py-2">{header}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`${title}-${rowIndex}`} className="border-b border-[var(--border-surface)]">
                  {row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`} className="px-4 py-3">{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

function MesaBindingCard({ matterId, canEdit }: { matterId: string; canEdit: boolean }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<MesaBindingCreate>({
    mesa_tenant_id: '',
    workspace_id: '',
    dataset_id: '',
    agent_id: '',
  })
  const { data: binding, isLoading, error } = useGetMesaBinding<MesaBindingResponse, ApiError>(
    matterId,
    { query: { retry: false } },
  )
  const createBinding = useCreateMesaBinding<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success('Binding saved; MESA permission preflight queued')
        await queryClient.invalidateQueries({ queryKey: getGetMesaBindingQueryKey(matterId) })
      },
      onError: (mutationError) => toast.error(readableError(mutationError, 'Binding failed')),
    },
  })

  if (isLoading) {
    return <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">Loading MESA binding…</section>
  }
  if (binding) {
    return (
      <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold">MESA Core v4 binding</h3>
            <p className="mt-1 text-sm text-[var(--color-anthracite-400)]">
              Workspace {binding.workspace_id} · dataset {binding.dataset_id} · agent {binding.agent_id}
            </p>
          </div>
          <StatusBadge
            status={binding.provisioning_status === 'READY' ? 'success' : binding.last_error ? 'error' : 'neutral'}
            label={binding.provisioning_status}
          />
        </div>
        {binding.last_error && <p className="mt-4 text-sm text-red-400">{binding.last_error}</p>}
        <p className="mt-4 text-xs text-[var(--color-anthracite-500)]">
          Law performs preflight only. ACL provisioning remains an external mesa-v4-admin onboarding task.
        </p>
      </section>
    )
  }

  if (!(error instanceof ApiError && error.status === 404)) {
    return (
      <section className="glass-card flex gap-3 rounded-xl border border-red-500/20 p-6 text-red-400">
        <AlertTriangle className="h-5 w-5 shrink-0" />
        {readableError(error, 'MESA binding status could not be loaded')}
      </section>
    )
  }

  return (
    <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">
      <h3 className="font-semibold">Bind pre-provisioned MESA Core v4 scope</h3>
      <p className="mt-1 text-sm text-[var(--color-anthracite-400)]">
        Enter identifiers already provisioned by mesa-v4-admin. This action is immutable.
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <BindingInput
          label="mesa_tenant_id"
          value={form.mesa_tenant_id}
          disabled={!canEdit || createBinding.isPending}
          onChange={(value) => setForm((current) => ({ ...current, mesa_tenant_id: value }))}
        />
        <BindingInput
          label="workspace_id"
          value={form.workspace_id}
          disabled={!canEdit || createBinding.isPending}
          onChange={(value) => setForm((current) => ({ ...current, workspace_id: value }))}
        />
        <BindingInput
          label="dataset_id"
          value={form.dataset_id}
          disabled={!canEdit || createBinding.isPending}
          onChange={(value) => setForm((current) => ({ ...current, dataset_id: value }))}
        />
        <BindingInput
          label="agent_id"
          value={form.agent_id}
          disabled={!canEdit || createBinding.isPending}
          onChange={(value) => setForm((current) => ({ ...current, agent_id: value }))}
        />
      </div>
      <Button
        className="mt-4"
        disabled={!canEdit || createBinding.isPending || Object.values(form).some((value) => !value.trim())}
        onClick={() => createBinding.mutate({ matterId, data: form })}
      >
        Save binding and run preflight
      </Button>
    </section>
  )
}

function BindingInput({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string
  value: string
  disabled: boolean
  onChange: (value: string) => void
}) {
  return (
    <input
      aria-label={label}
      placeholder={label}
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      className="rounded-md border border-[var(--border-surface)] bg-[var(--bg-surface)] px-3 py-2 text-sm"
    />
  )
}
