'use client'

import Link from 'next/link'
import { useState } from 'react'
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

interface QAResult {
  id: number
  question: string
  response?: QAResponse
  error?: string
  traceId?: string
}

function degradedMessage(reason: string | null | undefined): string | null {
  if (!reason) return null
  if (reason === 'MESA_SCOPE_NOT_READY') return 'MESA dataset kapsamı henüz hazır değil; yalnız doğrulanmış yerel canonical kaynaklar tarandı.'
  if (reason === 'MESA_NO_VERIFIED_EVIDENCE' || reason === 'MESA_PROVENANCE_UNVERIFIED') return 'MESA sonucu yerel canonical provenance ile doğrulanamadı; doğrulanamayan kaynaklar elendi.'
  if (reason === 'NO_VERIFIED_EVIDENCE') return 'Matter kapsamında cevap üretmeye yeterli doğrulanmış kaynak bulunamadı.'
  if (reason.startsWith('MESA_UNAVAILABLE')) return 'MESA Core şu anda erişilemiyor. PostgreSQL canonical kayıtları korunuyor; yalnız doğrulanmış yerel fallback kullanıldı.'
  return reason
}

function citationHref(citation: QACitation): string {
  const query = new URLSearchParams({
    revision: citation.revision_id,
    chunk: citation.chunk_id,
    start: String(citation.text_start),
    end: String(citation.text_end),
  })
  if (citation.page_number) query.set('page', String(citation.page_number))
  return `/documents/${citation.document_id}?${query.toString()}`
}

function CitationCard({ citation, index }: { citation: QACitation; index: number }) {
  return (
    <li className="rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Kaynak {index + 1} · Belge {citation.document_id.slice(0, 8)}</p>
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
          {citation.low_provenance ? 'Doğrulanmış PDF sayfası yok' : `Sayfa ${citation.page_number}`}
          {citation.relevance_score !== null && citation.relevance_score !== undefined
            ? ` · Kaynak eşleşme skoru ${citation.relevance_score.toFixed(3)}`
            : ''}
        </span>
        <Button render={<Link href={citationHref(citation)} />} variant="link" size="sm">
          Kaynakta aç
        </Button>
      </div>
      <p className="technical-id mt-2 break-all text-[0.68rem] text-foreground-muted">SHA-256 {citation.evidence_sha256}</p>
    </li>
  )
}

export function QAShell({ matterId }: { matterId: string }) {
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
                ? { ...result, error: error.referenceId ? `${error.message} · Referans ${error.referenceId}` : error.message }
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
            <h2 className="flex items-center gap-2 text-base font-semibold"><BookOpen className="size-4 text-primary" /> Kaynaklı matter sorgusu</h2>
            <p className="mt-1 text-sm text-foreground-secondary">Yanıtlar yalnız aktif matter kapsamı ve doğrulanmış canonical kaynaklarla oluşturulur.</p>
          </div>
          <StatusBadge status="verified" label="Fail-closed citation" />
        </PanelHeader>
        <PanelBody>
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="block space-y-1.5">
              <span className="text-sm font-medium">Sorunuz</span>
              <Textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Örneğin: Sözleşmedeki fesih koşulları hangi belgelerde yer alıyor?"
                className="min-h-24"
                disabled={qaMutation.isPending}
              />
            </label>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-foreground-muted">Doğrulanmış kanıt yoksa sistem yanıt uydurmaz ve abstain döndürür.</p>
              <Button type="submit" disabled={qaMutation.isPending || !question.trim()}>
                {qaMutation.isPending ? <Loader2 className="animate-spin" /> : <Search />} Kaynaklarda ara
              </Button>
            </div>
          </form>
        </PanelBody>
      </Panel>

      {results.length === 0 && (
        <InlineAlert tone="info" title="Sorgu kapsamı">
          <p>Dataset, engine, doğrulanmış belge/citation sayısı, işlem süresi ve trace kimliği her sonucun yanında gösterilir.</p>
        </InlineAlert>
      )}

      <div className="space-y-5" aria-live="polite">
        {results.map((result) => {
          const response = result.response
          const citations = response?.citations ?? []
          const degraded = degradedMessage(response?.degraded_reason)
          return (
            <article key={result.id} className="overflow-hidden rounded-lg border border-border bg-surface">
              <header className="border-b border-border bg-surface-subtle px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">Soru</p>
                <h2 className="mt-1 text-base font-semibold">{result.question}</h2>
              </header>
              <div className="space-y-6 p-5">
                {!response && !result.error && (
                  <div className="flex items-center gap-2 text-sm text-foreground-secondary" role="status">
                    <Loader2 className="size-4 animate-spin" /> Canonical kaynaklar doğrulanıyor
                  </div>
                )}
                {result.error && <InlineAlert tone="danger" title="Sorgu tamamlanamadı"><p>{result.error}</p></InlineAlert>}
                {response && (
                  <>
                    <section aria-labelledby={`answer-${result.id}`}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 id={`answer-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">Sonuç</h3>
                        <StatusBadge
                          status={response.status === 'ANSWERED' ? 'verified' : response.status === 'DEGRADED' ? 'degraded' : 'warning'}
                          label={response.status}
                        />
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-7">{response.answer}</p>
                    </section>

                    <section aria-labelledby={`basis-${result.id}`}>
                      <h3 id={`basis-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">Dayanaklar</h3>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <div className="rounded-md border border-border p-3"><FileSearch className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">Kapsam</p><p className="mt-1 text-sm font-medium">{response.retrieval?.scope ?? 'MATTER'}</p></div>
                        <div className="rounded-md border border-border p-3"><ShieldCheck className="mb-2 size-4 text-verified" /><p className="text-xs text-foreground-muted">Engine</p><p className="mt-1 text-sm font-medium">{response.retrieval?.engine ?? 'NONE'}</p></div>
                        <div className="rounded-md border border-border p-3"><BookOpen className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">Doğrulanmış kaynak</p><p className="tabular-nums mt-1 text-sm font-medium">{response.retrieval?.verified_document_count ?? 0} belge · {response.retrieval?.verified_citation_count ?? citations.length} citation</p></div>
                        <div className="rounded-md border border-border p-3"><Clock3 className="mb-2 size-4 text-primary" /><p className="text-xs text-foreground-muted">İşlem süresi</p><p className="tabular-nums mt-1 text-sm font-medium">{response.retrieval?.duration_ms ?? 0} ms</p></div>
                      </div>
                      {response.retrieval?.dataset_id && <p className="technical-id mt-2 text-xs text-foreground-muted">Dataset {response.retrieval.dataset_id}</p>}
                      {result.traceId && <p className="technical-id mt-1 text-xs text-foreground-muted">Trace {result.traceId}</p>}
                    </section>

                    <section aria-labelledby={`uncertainty-${result.id}`}>
                      <h3 id={`uncertainty-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">Belirsizlik ve eksik bilgi</h3>
                      {degraded ? (
                        <InlineAlert tone={response.status === 'ABSTAIN' ? 'warning' : 'info'} title={response.status === 'ABSTAIN' ? 'Yanıt üretilmedi' : 'Degraded çalışma'} className="mt-3">
                          <p>{degraded}</p>
                        </InlineAlert>
                      ) : (
                        <p className="mt-2 text-sm text-foreground-secondary">Backend ek bir belirsizlik veya çelişki bilgisi bildirmedi.</p>
                      )}
                    </section>

                    <section aria-labelledby={`sources-${result.id}`}>
                      <h3 id={`sources-${result.id}`} className="text-sm font-semibold uppercase tracking-wide text-foreground-muted">Kaynaklar</h3>
                      {citations.length > 0 ? (
                        <ol className="mt-3 space-y-3">
                          {citations.map((citation, index) => (
                            <CitationCard key={`${citation.revision_id}:${citation.chunk_id}:${citation.text_start}`} citation={citation} index={index} />
                          ))}
                        </ol>
                      ) : (
                        <div className="mt-3 flex items-center gap-2 text-sm text-foreground-secondary"><AlertTriangle className="size-4 text-warning" /> Doğrulanmış citation bulunmuyor.</div>
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
