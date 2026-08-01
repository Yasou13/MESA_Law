import { useListClaimsWithEvidence } from '@/api/endpoints/default/default';
import { AlertCircle, ShieldAlert } from 'lucide-react';

export function ClaimsEvidence({ matterId = "1" }: { matterId?: string }) {
  const { data: claimsResponse, isLoading: loading } = useListClaimsWithEvidence(matterId);
  const claims = Array.isArray(claimsResponse) ? claimsResponse : [];

  if (loading) {
    return (
      <div className="p-6 animate-pulse space-y-4">
        {[1, 2].map(i => (
          <div key={i} className="bg-[var(--bg-surface)] border border-[var(--border-surface)] p-4 rounded-xl h-24 shadow-sm"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6 text-[var(--foreground)]">Claims & Evidence Review</h2>
      <div className="space-y-4">
        {claims.map((claim) => (
          <div key={claim.id} className="bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl p-5 flex flex-col md:flex-row gap-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider mb-2">Extracted Claim</h3>
              <p className="text-[var(--foreground)] leading-relaxed">{claim.claim}</p>
              <div className="mt-4 flex gap-2">
                <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${claim.confidence === 'high' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : claim.confidence === 'medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                  {claim.confidence || 'Medium'} Confidence
                </span>
                <span className="text-xs px-2.5 py-1 rounded-full border font-medium bg-[var(--color-anthracite-800)] text-[var(--color-anthracite-300)] border-[var(--color-anthracite-700)]">
                  PROPOSED
                </span>
              </div>
            </div>
            
            <div className="w-px bg-[var(--border-surface)] hidden md:block"></div>
            
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider mb-2">Supporting Evidence</h3>
              {claim.evidence ? (
                <div className="bg-[var(--color-anthracite-900)] p-3 rounded-lg border border-[var(--border-surface)]">
                  <p className="text-[var(--color-anthracite-200)] text-sm italic">"{claim.evidence}"</p>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[var(--color-anthracite-400)] text-sm italic p-3 bg-[var(--bg-surface-hover)] rounded-lg border border-[var(--border-surface)] border-dashed">
                  <AlertCircle className="w-4 h-4" />
                  No explicit supporting evidence found in source documents
                </div>
              )}
            </div>
          </div>
        ))}
        {claims.length === 0 && (
          <div className="text-center p-12 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl border-dashed">
            <ShieldAlert className="w-12 h-12 text-[var(--color-anthracite-500)] mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No Claims Extracted</h3>
            <p className="text-[var(--color-anthracite-400)]">Upload documents to begin automated claim extraction.</p>
          </div>
        )}
      </div>
    </div>
  );
}
