'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import {
  AlertTriangle,
  BookOpen,
  Clock3,
  FileSearch,
  Loader2,
  Search,
  ShieldCheck,
} from 'lucide-react'

import { useAskQuestion } from '@/api/endpoints/qa/qa'
import type { QACitation, QAResponse } from '@/api/models'
import { Button } from '@/components/ui/button'
import { InlineAlert } from '@/components/ui/inline-alert'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { SourceBadge } from '@/components/ui/source-badge'
import { StatusBadge } from '@/components/ui/status-badge'
import { Textarea } from '@/components/ui/textarea'
import { ApiError, getApiResponseMetadata } from '@/lib/api/client'
import { localizedHref, type AppLocale } from '@/lib/navigation'

interface QAResult {
  id: number
  question: string
  response?: QAResponse
  error?: string
  traceId?: string
}

function degradedMessage(reason: string | null | undefined, translate: (key: string) => string): string | null {
  if (!reason) return null
  if (reason === 'MESA_SCOPE_NOT_READY') return translate('scopeNotReady')
  if (reason === 'MESA_NO_VERIFIED_EVIDENCE' || reason === 'MESA_PROVENANCE_UNVERIFIED') return translate('provenanceUnverified')
  if (reason === 'NO_VERIFIED_EVIDENCE') return translate('noEvidence')
  if (reason.startsWith('MESA_UNAVAILABLE')) return translate('mesaUnavailable')
  return reason
}

function citationHref(citation: QACitation, locale: AppLocale): string {
  const query = new URLSearchParams({
    revision: citation.revision_id,
    chunk: citation.chunk_id,
    start: String(citation.text_start),
    end: String(citation.text_end),
  })
  if (citation.page_number) query.set('page', String(citation.page_number))
  return localizedHref(locale, `/documents/${citation.document_id}?${query.toString()}`)
}

function CitationCard({ citation, index }: { citation: QACitation; index: number }) {
  const t = useTranslations('QA')
  const locale = useLocale() as AppLocale
  return (
    <li className="rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{t('source', { index: index + 1, document: citation.document_id.slice(0, 8) })}</p>
          <p className="technical-id mt-1 text-xs text-foreground-muted">
            rev {citation.revision_id.slice(0, 8)} · chunk {citation.chunk_id.slice(0, 8)} · {citation.text_start}–{citation.text_end}
          </p>
        </div>
        <SourceBadge lowProvenance={citation.low_provenance} />
      </div>
      <blockquote className="legal-reading mt-3 border-l-2 border-primary pl-3 text-sm leading-6">
        {citation.evidence_excerpt}
      </blockquote>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-foreground-muted">
        <span>
          {citation.low_provenance ? t('lowPage') : t('page', { page: citation.page_number ?? '—' })}
          {citation.relevance_score !== null && citation.relevance_score !== undefined
            ? ` · ${t('relevance', { score: citation.relevance_score.toFixed(3) })}`
            : ''}
        </span>
        <Button render={<Link href={citationHref(citation, locale)} />} variant="link" size="sm">
          {t('openSource')}
        </Button>
      </div>
      <p className="technical-id mt-2 break-all text-[0.68rem] text-foreground-muted">SHA-256 {citation.evidence_sha256}</p>
    </li>
  )
}

export function QAShell({ matterId }: { matterId: string }) {
  const t = useTranslations('QA')
  const [question, setQuestion] = useState('')
  const [results, setResults] = useState<QAResult[]>([])
  const qaMutation = useAskQuestion<ApiError>()

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const submittedQuestion = question.trim()
    if (!submittedQuestion) return
    const resultId = Date.now()
    setQuestion('')
    setResults((current) => [{ id: resultId, question: submittedQuestion }, ...current])
    qaMutation.mutate(
      { data: { matter_id: matterId, question: submittedQuestion } },
      {
        onSuccess: (response) => {
          const metadata = getApiResponseMetadata(response)
          setResults((current) =>
            current.map((result) =>
              result.id === resultId
                ? { ...result, response, traceId: metadata?.traceId ?? metadata?.correlationId }
                : result,
            ),
          )
        },
        onError: (error) => {
          setResults((current) =>
            current.map((result) =>
              result.id === resultId
                ? { ...result, error: error.referenceId ? `${error.message} · ${t('reference')} ${error.referenceId}` : error.message }
                : result,
            ),
          )
        },
      },
    )
  }

  return (
    <div className="space-y-5">
      <Panel>
        <PanelHeader className="items-start">
          <div>
            <h2 className="flex items-center gap-2 text-base font-semibold"><BookOpen className="size-4 text-primary" />{t('queryTitle')}</h2>
            <p className="mt-1 text-sm text-foreground-secondary">{t('queryDescription')}</p>
          </div>
          <StatusBadge status="verified" label={t('failClosed')} />
        </PanelHeader>
        <PanelBody>
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="block space-y-1.5">
              <span className="text-sm font-medium">{t('question')}</span>
              <Textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder={t('placeholder')}
                className="min-h-24"
                disabled={qaMutation.isPending}
              />
            </label>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-foreground-muted">{t('abstainNote')}</p>
              <Button type="submit" disabled={qaMutation.isPending || !question.trim()}>
                {qaMutation.isPending ? <Loader2 className="animate-spin" /> : <Search />}{t('search')}
              </Button>
            </div>
          </form>
        </PanelBody>
      </Panel>

      {results.length === 0 && (
        <InlineAlert tone="info" title={t('scopeTitle')}>
          <p>{t('scopeDescription')}</p>
        </InlineAlert>
      )}

      <div className="space-y-5" aria-live="polite">
        {results.map((result) => {
          const response = result.response
          const citations = response?.citations ?? []
          const degraded = degradedMessage(response?.degraded_reason, t)
          return (
            <article key={result.id} className="overflow-hidden rounded-lg border border-border bg-surface">
              <header className="border-b border-border bg-surface-subtle px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">{t('question')}</p>
                <h2 className="mt-1 text-base font-semibold">{result.question}</h2>
              </header>
              <div className="space-y-6 p-5">
                {!response && !result.error && (
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary" role="status">
                    <Loader2 className="size-4 animate-spin" />{t('verifying')}
                  </div>
                )}
                {result.error && <InlineAlert tone="danger" title={t('failed')}><p>{result.error}</p></InlineAlert>}
                {response && (
                  <>
                    <section aria-labelledby={`answer-${result.id}`}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 id={`answer-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">{t('result')}</h3>
                        <StatusBadge
                          status={response.status === 'ANSWERED' ? 'verified' : response.status === 'DEGRADED' ? 'degraded' : 'warning'}
                          label={response.status}
                        />
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7">{response.answer}</p>
                    </section>

                    <section aria-labelledby={`basis-${result.id}`}>
                      <h3 id={`basis-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">{t('basis')}</h3>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-md border border-border p-3"><FileSearch className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">{t('scope')}</p><p className="mt-1 text-sm font-medium">{response.retrieval?.scope ?? 'MATTER'}</p></div>
                        <div className="rounded-md border border-border p-3"><ShieldCheck className="mb-2 size-4 text-verified" /><p className="text-xs text-foreground-muted">Engine</p><p className="mt-1 text-sm font-medium">{response.retrieval?.engine ?? 'NONE'}</p></div>
                        <div className="rounded-md border border-border p-3"><BookOpen className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">{t('verifiedSource')}</p><p className="tabular-nums mt-1 text-sm font-medium">{t('sourceCount', { documents: response.retrieval?.verified_document_count ?? 0, citations: response.retrieval?.verified_citation_count ?? citations.length })}</p></div>
                        <div className="rounded-md border border-border p-3"><Clock3 className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">{t('duration')}</p><p className="tabular-nums mt-1 text-sm font-medium">{response.retrieval?.duration_ms ?? 0} ms</p></div>
                      </div>
                      {response.retrieval?.dataset_id && <p className="technical-id mt-2 text-xs text-foreground-muted">Dataset {response.retrieval.dataset_id}</p>}
                      {result.traceId && <p className="technical-id mt-1 text-xs text-foreground-muted">Trace {result.traceId}</p>}
                    </section>

                    <section aria-labelledby={`uncertainty-${result.id}`}>
                      <h3 id={`uncertainty-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">{t('uncertainty')}</h3>
                      {degraded ? (
                        <InlineAlert tone={response.status === 'ABSTAIN' ? 'warning' : 'info'} title={response.status === 'ABSTAIN' ? t('noAnswer') : t('degraded')} className="mt-3">
                          <p>{degraded}</p>
                        </InlineAlert>
                      ) : (
                        <p className="mt-2 text-sm text-foreground-secondary">{t('noExtraUncertainty')}</p>
                      )}
                    </section>

                    <section aria-labelledby={`sources-${result.id}`}>
                      <h3 id={`sources-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">{t('sources')}</h3>
                      {citations.length > 0 ? (
                        <ol className="mt-3 space-y-3">
                          {citations.map((citation, index) => (
                            <CitationCard key={`${citation.revision_id}:${citation.chunk_id}:${citation.text_start}`} citation={citation} index={index} />
                          ))}
                        </ol>
                      ) : (
                        <div className="mt-3 flex items-center gap-2 text-sm text-foreground-secondary"><AlertTriangle className="size-4 text-warning" />{t('noCitations')}</div>
                      )}
                    </section>
                  </>
                )}
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}
