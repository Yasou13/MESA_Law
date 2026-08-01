import { AlertCircle, Book } from 'lucide-react'

export function ResearchShell({ matterId }: { matterId: string }) {
  return (
    <section className="glass-card rounded-xl border border-[var(--border-surface)] p-8">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-[var(--color-lila-500)]/20 bg-[var(--color-lila-500)]/10">
          <Book className="h-5 w-5 text-[var(--color-lila-500)]" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-[var(--foreground)]">External legal research unavailable</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[var(--color-anthracite-400)]">
            External case-law and legislation research is outside the current MVP and is disabled by default. No research job will be queued for matter {matterId.slice(0, 8)}.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-sm text-amber-500">
            <AlertCircle className="h-4 w-4" /> Feature flag: OFF
          </div>
        </div>
      </div>
    </section>
  )
}
