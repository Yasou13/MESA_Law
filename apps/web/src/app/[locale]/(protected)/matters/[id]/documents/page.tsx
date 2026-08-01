'use client'

import type { ColumnDef } from '@tanstack/react-table'
import { useQueryClient } from '@tanstack/react-query'
import { Download, ExternalLink, Loader2, UploadCloud } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { use, useMemo, useRef, useState } from 'react'
import { toast } from 'react-hot-toast'

import {
  downloadDocument,
  getListMatterDocumentsQueryKey,
  useCompleteUpload,
  useCreateUploadIntent,
  useListMatterDocuments,
} from '@/api/endpoints/default/default'
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
  if (['clean', 'ready', 'processed'].includes(status.toLowerCase())) return 'success'
  if (['failed', 'rejected', 'malicious'].includes(status.toLowerCase())) return 'danger'
  return 'processing'
}

export default function MatterDocumentsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: matterId } = use(params)
  const t = useTranslations('MatterDocuments')
  const documentsT = useTranslations('Documents')
  const common = useTranslations('Common')
  const tableCopy = useTranslations('DataTable')
  const locale = useLocale() as AppLocale
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadIntent = useCreateUploadIntent()
  const completeUpload = useCompleteUpload()
  const documentsQuery = useListMatterDocuments(matterId, {
    query: {
      refetchInterval: (query) => query.state.data?.some((document) => ['UPLOADING', 'SCANNING', 'PROCESSING'].includes(document.status.toUpperCase())) ? 3000 : false,
    },
  })

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setIsUploading(true)
    setUploadProgress(0)
    try {
      const intent = await uploadIntent.mutateAsync({ data: { matter_id: matterId, filename: file.name, mime_type: file.type || 'application/pdf', size_bytes: file.size } })
      setUploadProgress(50)
      const uploadResponse = await fetch(intent.presigned_url, { method: 'PUT', body: file, headers: { 'Content-Type': file.type || 'application/pdf' } })
      if (!uploadResponse.ok) throw new Error(t('storageRejected', { status: uploadResponse.status }))
      setUploadProgress(90)
      await completeUpload.mutateAsync({ documentId: intent.document_id })
      setUploadProgress(100)
      toast.success(t('uploaded'))
      await queryClient.invalidateQueries({ queryKey: getListMatterDocumentsQueryKey(matterId) })
    } catch (error: unknown) {
      toast.error(error instanceof Error ? error.message : t('uploadError'))
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const columns = useMemo<ColumnDef<DocumentResponse, unknown>[]>(() => [
    {
      accessorKey: 'title',
      header: ({ column }) => <SortableHeader label={documentsT('name')} column={column} />,
      cell: ({ row }) => <div><Link href={localizedHref(locale, `/documents/${row.original.id}`)} className="block max-w-[28rem] truncate font-medium text-primary hover:underline">{row.original.title}</Link><span className="technical-id text-foreground-muted">{row.original.id.slice(0, 12)}</span></div>,
    },
    {
      accessorKey: 'status',
      header: ({ column }) => <SortableHeader label={common('status')} column={column} />,
      cell: ({ row }) => <StatusBadge status={documentTone(row.original.status)} label={row.original.status.toUpperCase()} />,
    },
    {
      accessorKey: 'provenance_state',
      header: documentsT('provenance'),
      cell: ({ row }) => <SourceBadge lowProvenance={row.original.provenance_state.toUpperCase() !== 'VERIFIED'} label={row.original.provenance_state.replaceAll('_', ' ')} />,
    },
    {
      accessorKey: 'created_at',
      header: ({ column }) => <SortableHeader label={common('createdAt')} column={column} />,
      cell: ({ row }) => new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(row.original.created_at)),
    },
    {
      id: 'actions',
      header: () => <span className="sr-only">{common('actions')}</span>,
      cell: ({ row }) => <div className="flex justify-end gap-1">
        <Link href={localizedHref(locale, `/documents/${row.original.id}`)} className={buttonVariants({ variant: 'ghost', size: 'icon-sm' })} aria-label={`${common('view')}: ${row.original.title}`}><ExternalLink className="size-4" /></Link>
        <Button variant="ghost" size="icon-sm" aria-label={`${common('download')}: ${row.original.title}`} onClick={async () => {
          try { const response = await downloadDocument(row.original.id); window.open(response.presigned_url, '_blank', 'noopener,noreferrer') }
          catch (error: unknown) { toast.error(error instanceof ApiError ? error.message : documentsT('downloadError')) }
        }}><Download className="size-4" /></Button>
      </div>,
    },
  ], [common, documentsT, locale])

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        description={t('description')}
        actions={<><Button onClick={() => fileInputRef.current?.click()} disabled={isUploading}>{isUploading ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}{isUploading ? t('uploading', { progress: uploadProgress }) : t('upload')}</Button><input ref={fileInputRef} type="file" className="sr-only" accept=".pdf,.docx,.txt" onChange={handleFileUpload} aria-label={t('upload')} /></>}
      />
      <p className="text-xs text-foreground-muted">{t('acceptedTypes')}</p>
      {documentsQuery.isLoading ? <LoadingState label={common('loading')} /> : documentsQuery.isError ? (
        <ErrorState title={documentsT('loadError')} description={documentsT('loadErrorDescription')} onRetry={() => documentsQuery.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={documentsQuery.data ?? []}
          getRowId={(row) => row.id}
          copy={{
            search: documentsT('search'), emptyTitle: documentsT('emptyTitle'), emptyDescription: t('emptyDescription'),
            previous: tableCopy('previous'), next: tableCopy('next'),
            page: (current, total) => tableCopy('page', { current, total }),
            rows: (visible, total) => tableCopy('rows', { visible, total }),
          }}
        />
      )}
    </div>
  )
}
