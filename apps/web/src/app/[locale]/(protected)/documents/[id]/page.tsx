'use client'

import dynamic from 'next/dynamic'
import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import {
  AlertTriangle,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Hash,
  ShieldCheck,
} from 'lucide-react'

import {
  useDownloadDocument,
  useGetDocumentViewerContext,
  useListParsedPages,
} from '@/api/endpoints/default/default'
import type {
  DocumentViewerContextResponse,
  DownloadResponse,
  ParsedPageResponse,
} from '@/api/models'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { SourceBadge } from '@/components/ui/source-badge'
import { StatusBadge } from '@/components/ui/status-badge'
import { ApiError } from '@/lib/api/client'
import { localizedHref, type AppLocale } from '@/lib/navigation'

const PdfDocumentSurface = dynamic(
  () => import('@/features/documents/components/PdfDocumentSurface'),
  {
    ssr: false,
    loading: () => <LoadingState label="PDF.js" />,
  },
)

interface FocusQuery {
  revisionId: string | null
  pageNumber: number | null
  chunkId: string | null
  textStart: number | null
  textEnd: number | null
}

interface LayoutBlock {
  characterStart: number
  characterEnd: number
  bbox: { x0: number; y0: number; x1: number; y1: number } | null
}

function finiteNumber(value: string | null): number | null {
  if (value === null || value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function readFocus(searchParams: Pick<URLSearchParams, 'get'>): FocusQuery {
  return {
    revisionId: searchParams.get('revision'),
    pageNumber: finiteNumber(searchParams.get('page')),
    chunkId: searchParams.get('chunk'),
    textStart: finiteNumber(searchParams.get('start')),
    textEnd: finiteNumber(searchParams.get('end')),
  }
}

function layoutBlocks(page: ParsedPageResponse | undefined): LayoutBlock[] {
  const layout = page?.layout_data
  if (!layout || typeof layout !== 'object') return []
  const rawBlocks = Reflect.get(layout, 'blocks')
  if (!Array.isArray(rawBlocks)) return []
  return rawBlocks.flatMap((rawBlock) => {
    if (!rawBlock || typeof rawBlock !== 'object') return []
    const start = Reflect.get(rawBlock, 'character_start')
    const end = Reflect.get(rawBlock, 'character_end')
    const rawBbox = Reflect.get(rawBlock, 'bbox')
    if (typeof start !== 'number' || typeof end !== 'number') return []
    const bbox =
      Array.isArray(rawBbox) &&
      rawBbox.length === 4 &&
      rawBbox.every((value) => typeof value === 'number' && Number.isFinite(value))
        ? { x0: rawBbox[0], y0: rawBbox[1], x1: rawBbox[2], y1: rawBbox[3] }
        : null
    return [{ characterStart: start, characterEnd: end, bbox }]
  })
}

function ParsedTextSurface({
  page,
  start,
  end,
  canHighlight,
}: {
  page: ParsedPageResponse | undefined
  start: number | null
  end: number | null
  canHighlight: boolean
}) {
  const t = useTranslations('Viewer')
  if (!page) {
    return <InlineAlert tone="warning" title={t('parsedNotReady')} />
  }
  const text = page.text_content
  const validSpan =
    canHighlight &&
    start !== null &&
    end !== null &&
    start >= 0 &&
    end > start &&
    end <= text.length

  return (
    <article className="legal-reading mx-auto max-w-3xl whitespace-pre-wrap border border-border bg-surface p-6 leading-8 shadow-sm md:p-10">
      {validSpan ? (
        <>
          {text.slice(0, start)}
          <mark className="rounded-sm bg-warning/25 text-foreground">{text.slice(start, end)}</mark>
          {text.slice(end)}
        </>
      ) : (
        text
      )}
    </article>
  )
}

export default function DocumentViewerPage() {
  const t = useTranslations('Viewer')
  const locale = useLocale() as AppLocale
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const documentId = params.id as string
  const focus = useMemo(() => readFocus(searchParams), [searchParams])
  const [selectedPage, setSelectedPage] = useState(focus.pageNumber ?? 1)
  const [pdfPageCount, setPdfPageCount] = useState(0)

  useEffect(() => {
    if (focus.pageNumber && focus.pageNumber > 0) setSelectedPage(focus.pageNumber)
  }, [focus.pageNumber])

  const contextQuery = useGetDocumentViewerContext<DocumentViewerContextResponse, ApiError>(documentId)
  const context = contextQuery.data
  const revision = context?.revision
  const parsedDocument = context?.parsed_document
  const parsedPagesQuery = useListParsedPages<ParsedPageResponse[], ApiError>(parsedDocument?.id ?? '', {
    query: { enabled: Boolean(parsedDocument?.id) },
  })
  const pages = parsedPagesQuery.data ?? []
  const selectedParsedPage = pages.find((page) => page.page_number === selectedPage)
  const canonicalReady = Boolean(revision?.id && revision.scan_status === 'READY')
  const downloadQuery = useDownloadDocument<DownloadResponse, ApiError>(documentId, {
    query: { enabled: canonicalReady },
  })

  const focusRequested = Boolean(
    focus.revisionId || focus.pageNumber || focus.chunkId || focus.textStart !== null || focus.textEnd !== null,
  )
  const matchingBlock = layoutBlocks(selectedParsedPage).find(
    (block) =>
      focus.textStart !== null &&
      focus.textEnd !== null &&
      block.characterStart <= focus.textStart &&
      block.characterEnd >= focus.textEnd,
  )
  const revisionMatches = Boolean(
    focus.revisionId &&
      revision?.id === focus.revisionId &&
      parsedDocument?.revision_id === focus.revisionId,
  )
  const pageMatches = Boolean(focus.pageNumber && selectedParsedPage?.page_number === focus.pageNumber)
  const focusVerified = Boolean(
    revisionMatches && pageMatches && focus.chunkId && matchingBlock && focus.textStart !== null && focus.textEnd !== null,
  )
  const pdfHighlight = focusVerified ? matchingBlock?.bbox : null
  const isPdf = revision?.mime_type === 'application/pdf'
  const pageCount = Math.max(pdfPageCount, pages.length, selectedPage)

  const selectPage = (page: number) => {
    setSelectedPage(page)
    const next = new URLSearchParams(searchParams.toString())
    next.set('page', String(page))
    next.delete('chunk')
    next.delete('start')
    next.delete('end')
    router.replace(`?${next.toString()}`, { scroll: false })
  }

  if (contextQuery.isLoading) return <LoadingState label={t('contextLoading')} />
  if (contextQuery.isError) {
    const error = contextQuery.error
    return (
      <ErrorState
        title={t('openError')}
        description={error.message}
        referenceId={error.referenceId}
        onRetry={() => contextQuery.refetch()}
      />
    )
  }
  if (!context) return null

  return (
    <div className="-m-4 flex min-h-[calc(100dvh-4rem)] flex-col border border-border bg-background md:-m-6 lg:-m-8">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <Button render={<Link href={localizedHref(locale, '/documents')} />} variant="ghost" size="icon-sm" aria-label={t('back')}>
            <ArrowLeft />
          </Button>
          <FileText className="size-5 shrink-0 text-primary" aria-hidden="true" />
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold">{context.document.title}</h1>
            <p className="technical-id truncate text-xs text-foreground-muted">{documentId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={context.document.status} label={context.document.status} />
          {downloadQuery.data?.presigned_url && (
            <Button render={<a href={downloadQuery.data.presigned_url} download />} variant="outline" size="sm">
              <Download />{t('original')}
            </Button>
          )}
        </div>
      </header>

      {focusRequested && !focusVerified && (
        <InlineAlert
          tone="warning"
          title={t('focusMismatch')}
          className="m-3"
        >
          <p>{t('focusMismatchDescription')}</p>
        </InlineAlert>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[11rem_minmax(0,1fr)_21rem]">
        <aside className="border-b border-border bg-surface xl:border-b-0 xl:border-r" aria-label={t('pages')}>
          <div className="flex items-center justify-between border-b border-border-subtle px-3 py-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">{t('pages')}</span>
            <span className="tabular-nums text-xs text-foreground-muted">{pageCount}</span>
          </div>
          <div className="flex max-h-36 gap-2 overflow-auto p-3 xl:max-h-[calc(100dvh-10rem)] xl:flex-col">
            {Array.from({ length: pageCount }, (_, index) => index + 1).map((page) => (
              <button
                key={page}
                type="button"
                onClick={() => selectPage(page)}
                aria-current={selectedPage === page ? 'page' : undefined}
                className="flex min-w-20 items-center justify-between rounded-md border border-border px-3 py-2 text-sm hover:bg-surface-subtle aria-[current=page]:border-primary aria-[current=page]:bg-primary-soft aria-[current=page]:text-primary xl:w-full"
              >
                <span>{t('page')}</span><span className="tabular-nums font-semibold">{page}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="min-h-[32rem] min-w-0 overflow-hidden bg-surface-subtle">
          <div className="flex items-center justify-center gap-2 border-b border-border bg-surface px-3 py-2">
            <Button variant="ghost" size="icon-sm" onClick={() => selectPage(Math.max(1, selectedPage - 1))} disabled={selectedPage <= 1} aria-label={t('previousPage')}><ChevronLeft /></Button>
            <span className="tabular-nums text-sm">{selectedPage} / {pageCount}</span>
            <Button variant="ghost" size="icon-sm" onClick={() => selectPage(Math.min(pageCount, selectedPage + 1))} disabled={selectedPage >= pageCount} aria-label={t('nextPage')}><ChevronRight /></Button>
          </div>
          <div className="h-[calc(100%-3rem)] overflow-auto p-4">
            {isPdf && downloadQuery.data?.presigned_url ? (
              <PdfDocumentSurface
                file={downloadQuery.data.presigned_url}
                pageNumber={selectedPage}
                highlight={pdfHighlight}
                onPageCount={setPdfPageCount}
              />
            ) : isPdf && downloadQuery.isLoading ? (
              <LoadingState label={t('securePdfLoading')} />
            ) : isPdf ? (
              <InlineAlert tone="warning" title={t('pdfUnavailable')}>
                <p>{t('pdfUnavailableDescription')}</p>
              </InlineAlert>
            ) : (
              <div className="space-y-3">
                <InlineAlert tone="warning" title={t('lowMode')}>
                  <p>{t('lowModeDescription')}</p>
                </InlineAlert>
                <ParsedTextSurface
                  page={selectedParsedPage}
                  start={focus.textStart}
                  end={focus.textEnd}
                  canHighlight={focusVerified}
                />
              </div>
            )}
          </div>
        </main>

        <aside className="space-y-3 border-t border-border bg-background p-3 xl:border-l xl:border-t-0" aria-label={t('sourceInfo')}>
          <Panel>
            <PanelHeader><h2 className="text-sm font-semibold">{t('canonicalRevision')}</h2></PanelHeader>
            <PanelBody className="space-y-3 text-sm">
              {revision ? (
                <>
                  <div className="flex items-center justify-between gap-2"><span className="text-foreground-muted">{t('revision')}</span><span className="technical-id">v{revision.version} · {revision.id.slice(0, 8)}</span></div>
                  <div className="flex items-center justify-between gap-2"><span className="text-foreground-muted">MIME</span><span>{revision.mime_type}</span></div>
                  <div className="flex items-center justify-between gap-2"><span className="text-foreground-muted">{t('size')}</span><span className="tabular-nums">{revision.size_bytes ? `${(revision.size_bytes / 1024).toFixed(1)} KB` : t('unknown')}</span></div>
                  <SourceBadge
                    lowProvenance={revision.provenance_state === 'LOW_PROVENANCE'}
                    label={revision.provenance_state}
                  />
                  {revision.sha256 && <p className="technical-id break-all text-xs text-foreground-muted"><Hash className="mr-1 inline size-3" />{revision.sha256}</p>}
                </>
              ) : (
                <p className="text-sm text-foreground-muted">{t('revisionMissing')}</p>
              )}
            </PanelBody>
          </Panel>

          <Panel>
            <PanelHeader><h2 className="text-sm font-semibold">{t('parsingChain')}</h2></PanelHeader>
            <PanelBody className="space-y-2 text-sm">
              {parsedDocument ? (
                <>
                  <p><span className="text-foreground-muted">Parser:</span> {parsedDocument.parser}</p>
                  <p><span className="text-foreground-muted">{t('parsingRevision')}:</span> {parsedDocument.parsing_revision}</p>
                  <p><span className="text-foreground-muted">Pipeline:</span> {parsedDocument.pipeline_version ?? t('unknown')}</p>
                  <p><span className="text-foreground-muted">OCR:</span> {parsedDocument.ocr_version ?? t('notUsed')}</p>
                  <StatusBadge status={parsedDocument.status} label={parsedDocument.status} />
                </>
              ) : <p className="text-foreground-muted">{t('parsedMissing')}</p>}
            </PanelBody>
          </Panel>

          {focusRequested && (
            <Panel>
              <PanelHeader><h2 className="text-sm font-semibold">{t('citationFocus')}</h2>{focusVerified && <ShieldCheck className="size-4 text-verified" />}</PanelHeader>
              <PanelBody className="space-y-2 text-xs">
                <p><span className="text-foreground-muted">{t('revision')}:</span> <span className="technical-id">{focus.revisionId ?? '—'}</span></p>
                <p><span className="text-foreground-muted">Chunk:</span> <span className="technical-id">{focus.chunkId ?? '—'}</span></p>
                <p><span className="text-foreground-muted">{t('textRange')}:</span> <span className="tabular-nums">{focus.textStart ?? '—'}–{focus.textEnd ?? '—'}</span></p>
              </PanelBody>
            </Panel>
          )}

          {context.document.failure_reason && (
            <InlineAlert tone="danger" title={t('processingError')}><p>{context.document.failure_reason}</p></InlineAlert>
          )}
          {downloadQuery.isError && (
            <InlineAlert tone="danger" title={t('downloadError')}><p>{downloadQuery.error.message}</p></InlineAlert>
          )}
          {parsedPagesQuery.isError && (
            <InlineAlert tone="warning" title={t('pagesError')}><p>{t('highlightDisabled')}</p></InlineAlert>
          )}
          {!canonicalReady && <AlertTriangle className="size-4 text-warning" aria-hidden="true" />}
        </aside>
      </div>
    </div>
  )
}
