import React, { useState } from 'react';
import { useStartLegalResearch } from '@/api/endpoints/research/research';
import { Search, Loader2, Book, AlertCircle, CheckCircle2 } from 'lucide-react';

export function ResearchShell({ matterId = "1" }: { matterId?: string }) {
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);

  const startResearch = useStartLegalResearch();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setSearched(true);
    setJobId(null);
    
    startResearch.mutate(
      { data: { matter_id: matterId, query } },
      {
        onSuccess: (res: any) => {
          setJobId(res.data.job_id);
        },
        onError: (error) => {
          console.error("Research search failed:", error);
        }
      }
    );
  };

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center">
          <Book className="w-5 h-5 text-[var(--color-lila-500)]" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-[var(--foreground)]">Deep Legal Research</h2>
          <p className="text-sm text-[var(--color-anthracite-400)]">Search legislation, case law, and precedent</p>
        </div>
      </div>
      
      <form onSubmit={handleSearch} className="flex gap-3 mb-8 relative">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-[var(--color-anthracite-400)]" />
          </div>
          <input 
            type="text" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Describe your legal question or specify keywords..." 
            className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl pl-11 pr-4 py-3.5 text-sm text-[var(--foreground)] focus:outline-none focus:border-[var(--color-lila-500)] transition-colors shadow-sm placeholder:text-[var(--color-anthracite-500)]"
            disabled={startResearch.isPending}
          />
        </div>
        <button 
          type="submit" 
          disabled={startResearch.isPending || !query.trim()}
          className="bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] disabled:opacity-50 disabled:hover:bg-[var(--color-lila-600)] text-white px-8 py-3.5 rounded-xl text-sm font-medium transition-all shadow-sm flex items-center gap-2"
        >
          {startResearch.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
        </button>
      </form>

      {startResearch.isPending && (
        <div className="space-y-4">
          <div className="h-4 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded w-1/4 animate-pulse mb-6"></div>
          {[1, 2].map(i => (
            <div key={i} className="bg-[var(--bg-surface)] border border-[var(--border-surface)] p-6 rounded-xl shadow-sm animate-pulse">
              <div className="h-4 bg-[var(--color-anthracite-800)] rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-[var(--color-anthracite-800)] rounded w-full mb-3"></div>
              <div className="h-3 bg-[var(--color-anthracite-800)] rounded w-3/4"></div>
            </div>
          ))}
        </div>
      )}

      {startResearch.isError && (
        <div className="p-4 bg-[var(--color-semantic-error)]/10 border border-[var(--color-semantic-error)]/20 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-[var(--color-semantic-error)] shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-[var(--color-semantic-error)]">Failed to Start Research</h3>
            <p className="text-sm text-[var(--color-semantic-error)]/80 mt-1">An error occurred while queueing the research job. Please try again.</p>
          </div>
        </div>
      )}

      {startResearch.isSuccess && jobId && (
        <div className="p-8 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl flex flex-col items-center justify-center text-center shadow-sm">
          <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mb-4">
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
          </div>
          <h3 className="text-lg font-medium text-[var(--foreground)] mb-2">Research Job Queued</h3>
          <p className="text-[var(--color-anthracite-400)] max-w-md mx-auto mb-4">
            Our AI engine is currently scanning through the matter documents, case law databases, and legislation to find matches.
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg text-sm text-[var(--color-anthracite-300)] font-mono">
            Job ID: {jobId}
          </div>
        </div>
      )}

      {!searched && (
        <div className="text-center py-16 px-4 bg-[var(--bg-surface)] border border-[var(--border-surface)] border-dashed rounded-xl">
          <Book className="w-12 h-12 text-[var(--color-anthracite-500)] mx-auto mb-4 opacity-50" />
          <h3 className="text-base font-medium text-[var(--foreground)] mb-2">Start Legal Research</h3>
          <p className="text-[var(--color-anthracite-400)] max-w-sm mx-auto text-sm">
            Enter a query above to search across the entire legal database grounded in your current matter context.
          </p>
        </div>
      )}
    </div>
  );
}
