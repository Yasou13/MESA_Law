'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  Check,
  ChevronRight,
  FileSearch,
  History,
  Loader2,
  Search,
  X,
} from 'lucide-react'
import { toast } from 'react-hot-toast'

import { useGetDocumentViewerContext } from '@/api/endpoints/default/default'
import {
  getGetReviewContextQueryKey,
  getListReviewsQueryKey,
  useApproveReview,
  useCorrectReview,
  useGetReviewContext,
  useListReviews,
  useRejectReview,
} from '@/api/endpoints/reviews/reviews'
import type {
  DocumentViewerContextResponse,
  ReviewContextResponse,
  ReviewItemResponse,
} from '@/api/models'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { SourceBadge } from '@/components/ui/source-badge'
import { StatusBadge } from '@/components/ui/status-badge'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '@/lib/api/client'

type ReviewFilter = 'ALL' | 'PROPOSED' | 'PUBLISHING' | 'PUBLISHED' | 'REJECTED'

function errorMessage(error: ApiError): string {
  if (error.status === 409) return 'Bu inceleme başka bir kullanıcı tarafından güncellendi. Güncel sürüm yüklendi.'
  return error.referenceId ? `${error.message} · Referans ${error.referenceId}` : error.message
}

function queryForSource(source: NonNullable<ReviewContextResponse['source']>): string {
  const query = new URLSearchParams({ revision: source.revision_id })
  if (source.page_number) query.set('page', String(source.page_number))
  if (source.chunk_id) query.set('chunk', source.chunk_id)
  if (source.text_start !== null && source.text_start !== undefined) query.set('start', String(source.text_start))
  if (source.text_end !== null && source.text_end !== undefined) query.set('end', String(source.text_end))
  return query.toString()
}

function ReviewPayloadEditor({
  value,
  onChange,
  disabled,
}: {
  value: Record<string, unknown>
  onChange: (next: Record<string, unknown>) => void
  disabled: boolean
}) {
  const update = (key: string, nextValue: unknown) => onChange({ ...value, [key]: nextValue })
  const entries = Object.entries(value)
  if (entries.length === 0) return <p className="text-sm text-foreground-muted">Öneri alanı bulunmuyor.</p>

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {entries.map(([key, fieldValue]) => {
        const isNested = typeof fieldValue === 'object' && fieldValue !== null
        return (
          <label key={key} className={isNested ? 'space-y-1.5 md:col-span-2' : 'space-y-1.5'}>
            <span className="technical-id text-xs font-medium text-foreground-secondary">{key}</span>
            {isNested ? (
              <Textarea
                value={JSON.stringify(fieldValue, null, 2)}
                disabled={disabled}
                className="min-h-28 font-mono text-xs"
                onChange={(event) => {
                  try {
                    update(key, JSON.parse(event.target.value) as unknown)
                  } catch {
                    // Keep the last valid structured value; invalid JSON is never submitted.
                  }
                }}
              />
            ) : (
              <Input
                value={fieldValue === null || fieldValue === undefined ? '' : String(fieldValue)}
                disabled={disabled}
                onChange={(event) => {
                  const nextValue =
                    typeof fieldValue === 'number'
                      ? Number(event.target.value)
                      : typeof fieldValue === 'boolean'
                        ? event.target.value === 'true'
                        : event.target.value
                  update(key, nextValue)
                }}
              />
            )}
          </label>
        )
      })}
    </div>
  )
}

export function ReviewWorkspace({ matterId }: { matterId?: string }) {
  const queryClient = useQueryClient()
  const queryParams = matterId ? { matter_id: matterId } : undefined
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [filter, setFilter] = useState<ReviewFilter>('PROPOSED')
  const [search, setSearch] = useState('')
  const [correctedContent, setCorrectedContent] = useState<Record<string, unknown>>({})
  const [reason, setReason] = useState('')

  const reviewsQuery = useListReviews<ReviewItemResponse[], ApiError>(queryParams)
  const reviews = reviewsQuery.data ?? []
  const filteredReviews = useMemo(
    () =>
      reviews.filter((review) => {
        const matchesFilter =
          filter === 'ALL' ||
          review.status === filter ||
          (filter === 'PUBLISHING' && ['APPROVED', 'CORRECTED', 'PUBLISHING', 'PUBLICATION_FAILED'].includes(review.status))
        const haystack = `${review.entity_type} ${review.matter_id} ${review.id}`.toLocaleLowerCase('tr')
        return matchesFilter && haystack.includes(search.trim().toLocaleLowerCase('tr'))
      }),
    [filter, reviews, search],
  )

  useEffect(() => {
    if (selectedId && filteredReviews.some((review) => review.id === selectedId)) return
    setSelectedId(filteredReviews[0]?.id ?? null)
  }, [filteredReviews, selectedId])

  const selectedReview = reviews.find((review) => review.id === selectedId) ?? null
  const contextQuery = useGetReviewContext<ReviewContextResponse, ApiError>(selectedId ?? '', {
    query: { enabled: Boolean(selectedId) },
  })
  const reviewContext = contextQuery.data
  const source = reviewContext?.source
  const viewerQuery = useGetDocumentViewerContext<DocumentViewerContextResponse, ApiError>(
    source?.document_id ?? '',
    { query: { enabled: Boolean(source?.document_id) } },
  )
  const revisionMatches = Boolean(
    source &&
      viewerQuery.data?.revision?.id === source.revision_id &&
      viewerQuery.data.parsed_document?.revision_id === source.revision_id,
  )
  const locatorComplete = Boolean(
    source?.chunk_id &&
      source.evidence_text &&
      source.evidence_sha256 &&
      source.text_start !== null &&
      source.text_start !== undefined &&
      source.text_end !== null &&
      source.text_end !== undefined &&
      source.text_end > source.text_start,
  )
  const sourceReady = Boolean(contextQuery.isSuccess && viewerQuery.isSuccess && revisionMatches && locatorComplete)
  const canDecide = selectedReview?.status === 'PROPOSED' && sourceReady

  useEffect(() => {
    if (!selectedReview) return
    setCorrectedContent(selectedReview.corrected_content ?? selectedReview.proposed_content)
    setReason('')
  }, [selectedReview])

  const invalidate = async (reviewId: string) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: getListReviewsQueryKey(queryParams) }),
      queryClient.invalidateQueries({ queryKey: getGetReviewContextQueryKey(reviewId) }),
    ])
  }
  const onMutationError = async (error: ApiError) => {
    toast.error(errorMessage(error))
    if (error.status === 409 && selectedId) await invalidate(selectedId)
  }
  const approveMutation = useApproveReview<ApiError>({
    mutation: {
      onSuccess: async (_, variables) => {
        toast.success('İnceleme onaylandı; yayın kuyruğuna alındı.')
        await invalidate(variables.reviewId)
      },
      onError: onMutationError,
    },
  })
  const correctMutation = useCorrectReview<ApiError>({
    mutation: {
      onSuccess: async (_, variables) => {
        toast.success('Düzeltme kaydedildi; yayın kuyruğuna alındı.')
        await invalidate(variables.reviewId)
      },
      onError: onMutationError,
    },
  })
  const rejectMutation = useRejectReview<ApiError>({
    mutation: {
      onSuccess: async (_, variables) => {
        toast.success('İnceleme reddedildi.')
        await invalidate(variables.reviewId)
      },
      onError: onMutationError,
    },
  })
  const pending = approveMutation.isPending || correctMutation.isPending || rejectMutation.isPending

  const chooseNext = () => {
    if (!selectedId) return
    const currentIndex = filteredReviews.findIndex((review) => review.id === selectedId)
    setSelectedId(filteredReviews[currentIndex + 1]?.id ?? filteredReviews[0]?.id ?? null)
  }

  if (reviewsQuery.isLoading) return <LoadingState label="İnceleme kuyruğu yükleniyor" />
  if (reviewsQuery.isError) {
    return (
      <ErrorState
        title="İnceleme kuyruğu alınamadı"
        description={reviewsQuery.error.message}
        referenceId={reviewsQuery.error.referenceId}
        onRetry={() => reviewsQuery.refetch()}
      />
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">İnceleme Merkezi</h1>
        <p className="mt-1 text-sm text-foreground-secondary">
          Canonical kayda yalnız gerçek belge kaynağıyla eşleşen onaylı veya düzeltilmiş öneriler girer.
        </p>
      </div>

      <div className="grid min-h-[42rem] grid-cols-1 overflow-hidden rounded-lg border border-border bg-surface xl:grid-cols-[18rem_minmax(0,1fr)_22rem]">
        <aside className="border-b border-border xl:border-b-0 xl:border-r" aria-label="İnceleme kuyruğu">
          <div className="space-y-3 border-b border-border p-3">
            <label className="relative block">
              <Search className="absolute left-3 top-2.5 size-4 text-foreground-muted" aria-hidden="true" />
              <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Kuyrukta ara" className="pl-9" />
            </label>
            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value as ReviewFilter)}
              className="h-9 w-full rounded-md border border-border bg-surface px-3 text-sm"
              aria-label="İnceleme durumu"
            >
              <option value="PROPOSED">Önerilen</option>
              <option value="PUBLISHING">Onaylanan / yayınlanan</option>
              <option value="PUBLISHED">Yayınlandı</option>
              <option value="REJECTED">Reddedildi</option>
              <option value="ALL">Tümü</option>
            </select>
          </div>
          <div className="max-h-72 overflow-auto xl:max-h-[calc(100dvh-17rem)]">
            {filteredReviews.length === 0 ? (
              <NoDataState title="Bu kuyruk boş" description="Seçili filtrede inceleme bulunmuyor." />
            ) : (
              filteredReviews.map((review) => (
                <button
                  key={review.id}
                  type="button"
                  onClick={() => setSelectedId(review.id)}
                  aria-current={selectedId === review.id ? 'true' : undefined}
                  className="flex w-full items-start gap-3 border-b border-border-subtle px-3 py-4 text-left hover:bg-surface-subtle aria-[current=true]:bg-primary-soft"
                >
                  <FileSearch className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{review.entity_type}</span>
                    <span className="technical-id mt-1 block truncate text-xs text-foreground-muted">{review.matter_id.slice(0, 8)} · v{review.version_id}</span>
                    <StatusBadge status={review.status} label={review.status} className="mt-2 w-fit" />
                  </span>
                  <ChevronRight className="mt-1 size-4 text-foreground-muted" aria-hidden="true" />
                </button>
              ))
            )}
          </div>
        </aside>

        <main className="min-w-0 border-b border-border p-4 xl:border-b-0 xl:border-r xl:p-6">
          {!selectedReview ? (
            <NoDataState title="İnceleme seçilmedi" description="Kaynak ve öneri ayrıntısını görmek için kuyruktan kayıt seçin." />
          ) : contextQuery.isLoading ? (
            <LoadingState label="İnceleme kaynağı doğrulanıyor" />
          ) : contextQuery.isError ? (
            <ErrorState
              title="İnceleme bağlamı alınamadı"
              description={contextQuery.error.message}
              referenceId={contextQuery.error.referenceId}
              onRetry={() => contextQuery.refetch()}
            />
          ) : (
            <div className="space-y-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">Öneri şeması</p>
                  <h2 className="mt-1 text-lg font-semibold">{reviewContext?.suggestion?.suggestion_type ?? selectedReview.entity_type}</h2>
                  <p className="technical-id mt-1 text-xs text-foreground-muted">İnceleme {selectedReview.id} · v{selectedReview.version_id}</p>
                </div>
                <StatusBadge status={selectedReview.status} label={selectedReview.status} />
              </div>

              {!sourceReady && selectedReview.status === 'PROPOSED' && (
                <InlineAlert tone="warning" title="Karar işlemleri fail-closed durumda">
                  <p>Kaynak context yüklenmeden, locator eksiksiz olmadan ve canonical revision eşleşmeden onay, düzeltme veya red yapılamaz.</p>
                </InlineAlert>
              )}

              <ReviewPayloadEditor
                value={correctedContent}
                onChange={setCorrectedContent}
                disabled={selectedReview.status !== 'PROPOSED' || !sourceReady}
              />

              {selectedReview.status === 'PROPOSED' && (
                <label className="block space-y-1.5">
                  <span className="text-sm font-medium">Karar gerekçesi</span>
                  <Textarea
                    value={reason}
                    onChange={(event) => setReason(event.target.value)}
                    placeholder="Düzeltme ve red için en az 3 karakter zorunludur."
                    disabled={!sourceReady}
                  />
                </label>
              )}

              {selectedReview.decision_reason && (
                <InlineAlert tone="info" title="Kaydedilmiş karar gerekçesi"><p>{selectedReview.decision_reason}</p></InlineAlert>
              )}

              <div className="flex flex-wrap gap-2 border-t border-border pt-4">
                {selectedReview.status === 'PROPOSED' && (
                  <>
                    <Button
                      onClick={() => approveMutation.mutate({ reviewId: selectedReview.id, data: { expected_version: selectedReview.version_id } })}
                      disabled={!canDecide || pending}
                    >
                      {approveMutation.isPending ? <Loader2 className="animate-spin" /> : <Check />} Onayla
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => correctMutation.mutate({
                        reviewId: selectedReview.id,
                        data: {
                          expected_version: selectedReview.version_id,
                          corrected_content: correctedContent,
                          reason: reason.trim(),
                        },
                      })}
                      disabled={!canDecide || reason.trim().length < 3 || pending}
                    >
                      Düzelt ve onayla
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => rejectMutation.mutate({ reviewId: selectedReview.id, data: { expected_version: selectedReview.version_id, reason: reason.trim() } })}
                      disabled={!canDecide || reason.trim().length < 3 || pending}
                    >
                      <X /> Reddet
                    </Button>
                  </>
                )}
                <Button variant="ghost" onClick={chooseNext}>Daha sonra incele</Button>
              </div>
            </div>
          )}
        </main>

        <aside className="space-y-4 bg-background p-4" aria-label="Belge kaynağı">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">Belge kaynağı</p>
            <h2 className="mt-1 text-base font-semibold">Evidence ve provenance</h2>
          </div>
          {contextQuery.isLoading || viewerQuery.isLoading ? (
            <LoadingState label="Canonical revision doğrulanıyor" />
          ) : !source ? (
            <InlineAlert tone="warning" title="Legacy kaynak eksikliği">
              <p>Bu önerinin SourceLocator kaydı yok. Kaynak `null`; karar işlemleri kapalı.</p>
            </InlineAlert>
          ) : (
            <>
              {!revisionMatches && (
                <InlineAlert tone="danger" title="Revision uyuşmazlığı">
                  <p>Önerinin revision kimliği belgenin canonical revision’ı ile eşleşmiyor.</p>
                </InlineAlert>
              )}
              {!locatorComplete && (
                <InlineAlert tone="warning" title="Eksik locator">
                  <p>Chunk, metin aralığı veya evidence hash eksik olduğu için karar verilemez.</p>
                </InlineAlert>
              )}
              <Panel>
                <PanelHeader><h3 className="truncate text-sm font-semibold">{source.document_title}</h3></PanelHeader>
                <PanelBody className="space-y-3 text-sm">
                  <SourceBadge lowProvenance={source.provenance_state === 'LOW_PROVENANCE'} label={source.provenance_state} />
                  <p><span className="text-foreground-muted">Sayfa:</span> {source.page_number ?? 'Doğrulanmamış'}</p>
                  <p><span className="text-foreground-muted">Metin aralığı:</span> <span className="tabular-nums">{source.text_start ?? '—'}–{source.text_end ?? '—'}</span></p>
                  <p className="technical-id break-all text-xs text-foreground-muted">Chunk {source.chunk_id ?? '—'}</p>
                  <blockquote className="legal-reading border-l-2 border-primary pl-3 text-sm leading-6">
                    {source.evidence_text ?? 'Evidence metni yok.'}
                  </blockquote>
                  {source.evidence_sha256 && <p className="technical-id break-all text-[0.7rem] text-foreground-muted">SHA-256 {source.evidence_sha256}</p>}
                  <Button
                    render={<Link href={`/documents/${source.document_id}?${queryForSource(source)}`} />}
                    variant="outline"
                    size="sm"
                    className="w-full"
                  >
                    Kaynakta aç
                  </Button>
                </PanelBody>
              </Panel>
            </>
          )}

          {reviewContext?.suggestion && (
            <Panel>
              <PanelHeader><h3 className="text-sm font-semibold">Extraction</h3></PanelHeader>
              <PanelBody className="space-y-2 text-xs">
                <p>{reviewContext.suggestion.extractor_name} · {reviewContext.suggestion.extractor_version}</p>
                <p>Parser {reviewContext.suggestion.parser_version}</p>
                <p>Confidence category: {reviewContext.suggestion.confidence_category}</p>
              </PanelBody>
            </Panel>
          )}

          {reviewContext?.history && reviewContext.history.length > 0 && (
            <Panel>
              <PanelHeader><h3 className="flex items-center gap-2 text-sm font-semibold"><History className="size-4" /> Audit geçmişi</h3></PanelHeader>
              <PanelBody>
                <ol className="space-y-3 text-xs">
                  {reviewContext.history.map((entry) => (
                    <li key={entry.id} className="border-l border-border pl-3">
                      <p className="font-medium">{entry.action}</p>
                      <p className="technical-id text-foreground-muted">{entry.user_id} · {new Date(entry.created_at).toLocaleString('tr-TR')}</p>
                    </li>
                  ))}
                </ol>
              </PanelBody>
            </Panel>
          )}
          {viewerQuery.isError && (
            <InlineAlert tone="danger" title="Canonical belge doğrulanamadı"><p>{viewerQuery.error.message}</p></InlineAlert>
          )}
          {!sourceReady && source && <AlertTriangle className="size-4 text-warning" aria-hidden="true" />}
        </aside>
      </div>
    </div>
  )
}
