'use client'

import { useState } from 'react'
import { useSearchLegalResearch } from '@/api/endpoints/research/research'
import { Search, BookOpen, Scale, Landmark, FileText, ChevronRight, AlertCircle } from 'lucide-react'

export default function ResearchPage() {
  const [query, setQuery] = useState('')
  const [activeQuery, setActiveQuery] = useState('')

  const { data: res, isLoading, isError } = useSearchLegalResearch(
    { q: activeQuery },
    { query: { enabled: activeQuery.length > 0 } }
  )

  const results: any[] = (res?.data as any[]) || []

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setActiveQuery(query.trim())
    }
  }

  const getSourceIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'case_law': return <Scale className="w-5 h-5 text-indigo-400" />
      case 'legislation': return <Landmark className="w-5 h-5 text-emerald-400" />
      default: return <FileText className="w-5 h-5 text-blue-400" />
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Legal Research</h1>
        <p className="text-zinc-400">Search through internal and external legal sources, case law, and legislation.</p>
      </div>

      <div className="glass-card rounded-xl p-6 border border-[var(--border-surface)]">
        <form onSubmit={handleSearch} className="relative flex items-center">
          <Search className="absolute left-4 w-5 h-5 text-zinc-400" />
          <input 
            type="text" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search case law, statutes, internal precedents..."
            className="w-full bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-xl py-4 pl-12 pr-32 focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)] text-[var(--foreground)]"
          />
          <button 
            type="submit"
            disabled={!query.trim()}
            className="absolute right-2 px-6 py-2 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors disabled:opacity-50 font-medium"
          >
            Search
          </button>
        </form>
      </div>

      {activeQuery && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Search Results for <span className="text-[var(--color-lila-400)]">"{activeQuery}"</span>
            </h2>
            <span className="text-sm text-zinc-400">{results.length} results found</span>
          </div>

          {isLoading && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
            </div>
          )}

          {isError && (
             <div className="p-6 text-center text-red-500 bg-red-500/10 rounded-xl border border-red-500/20">
               <AlertCircle className="w-8 h-8 mx-auto mb-2" />
               <p>Failed to perform research. Please try again.</p>
             </div>
          )}

          {!isLoading && !isError && results.length === 0 && (
            <div className="glass-card rounded-xl p-12 text-center text-zinc-400">
              <BookOpen className="w-12 h-12 text-zinc-500/50 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No Sources Found</h3>
              <p>We couldn&apos;t find any legal sources matching your query.</p>
            </div>
          )}

          {!isLoading && !isError && results.length > 0 && (
            <div className="grid gap-4">
              {results.map((source: any) => (
                <div key={source.id} className="glass-card rounded-xl p-5 border border-[var(--border-surface)] hover:border-[var(--color-lila-500)]/30 transition-colors cursor-pointer group">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] flex items-center justify-center shrink-0">
                      {getSourceIcon(source.source_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          {source.source_type.replace('_', ' ')}
                        </span>
                        <span className="w-1 h-1 rounded-full bg-zinc-600"></span>
                        <span className="text-xs font-mono text-[var(--color-lila-400)] bg-[var(--color-lila-500)]/10 px-2 py-0.5 rounded">
                          {source.citation}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-[var(--foreground)] group-hover:text-[var(--color-lila-400)] transition-colors line-clamp-1">
                        {source.title}
                      </h3>
                      <p className="mt-2 text-sm text-zinc-400 line-clamp-3">
                        {source.content}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-zinc-500 group-hover:text-[var(--color-lila-400)] shrink-0 self-center transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
