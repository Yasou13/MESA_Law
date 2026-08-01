'use client'

import { useState } from 'react'
import { AlertCircle, BookOpen, Loader2, Send } from 'lucide-react'

import { useAskQuestion } from '@/api/endpoints/qa/qa'
import type { QACitation } from '@/api/models'
import { ApiError } from '@/lib/api/client'

interface QAMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: QACitation[]
  status?: string
  degradedReason?: string | null
}

export function QAShell({ matterId }: { matterId: string }) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<QAMessage[]>([])
  const qaMutation = useAskQuestion<ApiError>()

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const question = query.trim()
    if (!question) return
    setMessages((current) => [...current, { role: 'user', content: question }])
    setQuery('')
    qaMutation.mutate(
      { data: { matter_id: matterId, question } },
      {
        onSuccess: (response) => {
          setMessages((current) => [
            ...current,
            {
              role: 'assistant',
              content: response.answer,
              citations: response.citations,
              status: response.status,
              degradedReason: response.degraded_reason,
            },
          ])
        },
        onError: (error) => {
          const reference = error.referenceId ? ` Reference: ${error.referenceId}.` : ''
          setMessages((current) => [
            ...current,
            { role: 'assistant', status: 'ERROR', content: `${error.message}.${reference}` },
          ])
        },
      },
    )
  }

  return (
    <div className="flex h-[600px] flex-col overflow-hidden rounded-xl border border-[var(--border-surface)] bg-[var(--bg-surface)] shadow-sm">
      <div className="flex items-center justify-between border-b border-[var(--border-surface)] bg-[var(--bg-surface-hover)] p-4">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-[var(--color-lila-500)]" />
          <h2 className="text-sm font-semibold text-[var(--foreground)]">Sourced matter Q&A</h2>
        </div>
        <span className="rounded-full border border-[var(--color-lila-500)]/20 bg-[var(--color-lila-500)]/10 px-2.5 py-1 text-xs font-medium text-[var(--color-lila-400)]">
          Verified local provenance only
        </span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="mx-auto mt-10 max-w-md text-center text-sm text-[var(--color-anthracite-400)]">
            Answers are restricted to this matter&apos;s active dataset/session. If evidence cannot be verified against the canonical document revision, page, chunk and text span, the service abstains.
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[88%] rounded-2xl border p-4 text-sm shadow-sm ${
                message.role === 'user'
                  ? 'rounded-tr-sm border-[var(--color-anthracite-700)] bg-[var(--color-anthracite-800)] text-white'
                  : message.status === 'ANSWERED'
                    ? 'rounded-tl-sm border-[var(--border-surface)] bg-[var(--bg-surface-hover)] text-[var(--foreground)]'
                    : 'rounded-tl-sm border-amber-500/20 bg-amber-500/10 text-amber-500'
              }`}
            >
              {message.role === 'assistant' && message.status && message.status !== 'ANSWERED' && (
                <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider">
                  <AlertCircle className="h-3.5 w-3.5" /> {message.status}
                </div>
              )}
              {message.degradedReason && <p className="mb-2 text-xs">{message.degradedReason}</p>}
              <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
              {message.citations && message.citations.length > 0 && (
                <div className="mt-4 border-t border-[var(--border-surface)] pt-3">
                  <span className="mb-2 block text-xs font-semibold uppercase tracking-wider">Citations</span>
                  <ol className="space-y-3 text-xs">
                    {message.citations.map((citation) => (
                      <li key={`${citation.revision_id}:${citation.chunk_id}:${citation.text_start}`}>
                        <div className="font-medium text-[var(--color-lila-400)]">
                          Document {citation.document_id.slice(0, 8)} · revision {citation.revision_id.slice(0, 8)} ·{' '}
                          {citation.low_provenance
                            ? 'LOW_PROVENANCE (no verified page)'
                            : `page ${citation.page_number}`}
                        </div>
                        <div className="mt-1 text-[var(--color-anthracite-400)]">
                          Chunk {citation.chunk_id.slice(0, 8)} · chars {citation.text_start}–{citation.text_end} · SHA-256 {citation.evidence_sha256.slice(0, 12)}…
                        </div>
                        <blockquote className="mt-1 border-l-2 border-[var(--color-lila-500)] pl-2 text-[var(--color-anthracite-300)]">
                          {citation.evidence_excerpt}
                        </blockquote>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        ))}
        {qaMutation.isPending && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-[var(--border-surface)] bg-[var(--bg-surface-hover)] p-4">
              <Loader2 className="h-4 w-4 animate-spin text-[var(--color-lila-500)]" />
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-[var(--border-surface)] bg-[var(--bg-surface)] p-3">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a question about verified matter evidence…"
          className="flex-1 rounded-xl border border-[var(--border-surface)] bg-[var(--bg-surface-hover)] px-4 py-2 text-sm text-[var(--foreground)] focus:border-[var(--color-lila-500)] focus:outline-none"
          disabled={qaMutation.isPending}
        />
        <button
          type="submit"
          disabled={qaMutation.isPending || !query.trim()}
          className="flex min-w-12 items-center justify-center rounded-xl bg-[var(--color-lila-600)] px-4 py-2 text-white transition-colors hover:bg-[var(--color-lila-500)] disabled:opacity-50"
        >
          {qaMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </form>
    </div>
  )
}
