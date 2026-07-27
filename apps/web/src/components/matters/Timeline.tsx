import React from 'react';
import { useListTimelineEvents } from '@/api/endpoints/default/default';
import { Loader2, AlertCircle, Clock } from 'lucide-react';

export function Timeline({ matterId = "1" }: { matterId?: string }) {
  const { data: timelineResponse, isLoading: loading, error, refetch } = useListTimelineEvents(matterId);
  const events = Array.isArray(timelineResponse?.data) ? timelineResponse.data : [];

  if (loading) {
    return (
      <div className="p-8 animate-pulse space-y-6">
        <div className="h-4 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded w-1/4"></div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-4">
              <div className="w-2 h-full bg-[var(--bg-surface)] rounded"></div>
              <div className="h-16 bg-[var(--bg-surface)] rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-[var(--color-semantic-error)]/10 border border-[var(--color-semantic-error)] rounded-xl text-[var(--color-semantic-error)]">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="w-5 h-5" />
          <h3 className="font-semibold">Failed to load timeline</h3>
        </div>
        <p className="text-sm opacity-80 mb-4">Could not load the chronological timeline. Please try again.</p>
        <button onClick={() => refetch()} className="text-sm bg-[var(--color-semantic-error)]/20 hover:bg-[var(--color-semantic-error)]/30 px-4 py-2 rounded-lg font-medium transition-colors">Retry</button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xl font-semibold text-[var(--foreground)]">Chronological Timeline</h2>
        <div className="flex items-center gap-2 text-sm text-[var(--color-anthracite-400)]">
          <Clock className="w-4 h-4" />
          {events.length} Events
        </div>
      </div>
      
      <div className="relative border-l-2 border-[var(--border-surface)] ml-3 space-y-10">
        {events.map((evt: any) => (
          <div key={evt.id} className="pl-8 relative group">
            <div className="absolute w-4 h-4 bg-[var(--color-lila-500)] rounded-full -left-[9px] top-1.5 ring-4 ring-[var(--background)] group-hover:scale-125 transition-transform"></div>
            
            <div className="bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl p-5 shadow-sm group-hover:shadow-md transition-shadow relative">
              {/* Arrow */}
              <div className="absolute w-3 h-3 bg-[var(--bg-surface)] border-l border-b border-[var(--border-surface)] rotate-45 -left-[7px] top-2"></div>
              
              <div className="text-sm font-medium text-[var(--color-lila-400)] mb-2">{evt.date || new Date(evt.event_date).toLocaleDateString()}</div>
              <div className="text-[var(--foreground)] font-medium text-lg mb-3">{evt.title || evt.description}</div>
              
              <div className="flex items-center gap-3">
                <span className="text-xs px-2.5 py-1 bg-[var(--bg-surface-hover)] text-[var(--color-anthracite-300)] rounded-md border border-[var(--border-surface)] flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-anthracite-400)]"></span>
                  Source: {evt.source_document_id || 'System'}
                </span>
                <span className={`text-xs px-2.5 py-1 rounded-md border font-medium ${evt.confidence === 'high' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                  Confidence: {evt.confidence || 'Medium'}
                </span>
              </div>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <div className="pl-8 text-[var(--color-anthracite-400)] text-sm italic">
            No events found for this matter.
          </div>
        )}
      </div>
    </div>
  );
}

