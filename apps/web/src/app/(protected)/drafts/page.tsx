'use client'

import { useListAllDraftsApiV1DraftStudioDraftsGet } from '@/api/endpoints/draft-studio/draft-studio'
import { FileEdit, Clock, ChevronRight } from 'lucide-react'
import Link from 'next/link'

export default function DraftsPage() {
  const { data: res, isLoading, isError } = useListAllDraftsApiV1DraftStudioDraftsGet()

  const drafts = (res?.data as any[]) || []

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Draft Studio</h1>
        <p className="text-zinc-400">Manage and edit your legal documents and drafts.</p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
        </div>
      )}

      {!isLoading && !isError && drafts.length === 0 && (
        <div className="glass-card rounded-xl p-12 text-center text-zinc-400">
          <FileEdit className="w-12 h-12 text-zinc-500/50 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No Drafts</h3>
          <p>You haven&apos;t created any drafts yet. Start one from a Matter page.</p>
        </div>
      )}

      {!isLoading && !isError && drafts.length > 0 && (
        <div className="grid gap-4">
          {drafts.map((draft: any) => (
            <Link key={draft.id} href={`/drafts/${draft.id}`}>
              <div className="glass-card rounded-xl p-5 border border-[var(--border-surface)] hover:border-[var(--color-lila-500)]/30 transition-colors group">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] flex items-center justify-center shrink-0">
                      <FileEdit className="w-5 h-5 text-[var(--color-lila-400)]" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-[var(--foreground)] group-hover:text-[var(--color-lila-400)] transition-colors">
                        {draft.title || 'Untitled Draft'}
                      </h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-zinc-400">
                        <span className="font-mono bg-[var(--bg-surface-hover)] px-2 py-0.5 rounded">
                          Matter: {draft.matter_id}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Version {draft.version}
                        </span>
                        <span>
                          Updated: {new Date(draft.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-zinc-500 group-hover:text-[var(--color-lila-400)] self-center transition-colors" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
