'use client'

import { use, useState } from 'react'
import { useListClaimsWithEvidence } from '@/api/endpoints/default/default'
import { ArrowLeft, Loader2, AlertCircle, CheckCircle, ShieldAlert, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import Link from 'next/link'
import { StatusBadge } from '@/components/ui/status-badge'
import { Button } from '@/components/ui/button'

export default function MatterClaimsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  const { data: claimsResponse, isLoading: loading, isError, refetch } = useListClaimsWithEvidence(matterId)
  const claims = Array.isArray(claimsResponse) ? claimsResponse : []
  
  const [expandedClaim, setExpandedClaim] = useState<string | null>(null)

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Matter Overview
      </Link>
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Claims, Defenses & Legal Issues</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Review the AI-extracted claims and their supporting evidence for this matter.</p>
        </div>
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4 glass-card rounded-xl border border-[var(--border-surface)]">
            <Loader2 className="animate-spin h-8 w-8 text-[var(--color-lila-500)]" />
            <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading claims...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4 glass-card rounded-xl border border-[var(--border-surface)]">
            <AlertCircle className="w-12 h-12 text-[var(--color-semantic-error)]" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">Failed to load claims</h3>
            <Button variant="outline" onClick={() => refetch()}>Retry</Button>
          </div>
        ) : claims.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <ShieldAlert className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Claims Found</h3>
            <p className="text-[var(--color-anthracite-500)]">Upload documents to begin automated claim extraction.</p>
          </div>
        ) : (
          claims.map((claim: any) => {
            const isExpanded = expandedClaim === claim.id
            const evidenceCount = claim.evidence ? 1 : 0
            
            return (
              <div key={claim.id} className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden transition-all duration-200">
                <div 
                  className="p-5 flex items-center justify-between cursor-pointer hover:bg-[var(--bg-surface-hover)]"
                  onClick={() => setExpandedClaim(isExpanded ? null : claim.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-[var(--color-lila-500)]/10 text-[var(--color-lila-600)] dark:text-[var(--color-lila-400)] rounded-md border border-[var(--color-lila-500)]/20">
                        {claim.type || 'Claim'}
                      </span>
                      <StatusBadge 
                        status={claim.status === 'approved' ? 'success' : claim.status === 'rejected' ? 'error' : 'review-required'} 
                        label={claim.status || 'PENDING'} 
                      />
                      <span className={`text-xs px-2.5 py-1 rounded-md border font-medium ${claim.confidence === 'high' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : claim.confidence === 'medium' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-red-500/10 text-red-500 border-red-500/20'}`}>
                        {claim.confidence || 'Medium'} Confidence
                      </span>
                    </div>
                    <p className="text-[var(--foreground)] font-medium leading-relaxed max-w-4xl">
                      {claim.description || claim.claim}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-6 pl-4 ml-4 border-l border-[var(--border-surface)] shrink-0">
                    <div className="flex flex-col items-center justify-center">
                      <div className="flex items-center gap-1.5 text-[var(--color-lila-500)]">
                        <FileText className="w-5 h-5" />
                        <span className="font-bold text-lg">{evidenceCount}</span>
                      </div>
                      <span className="text-xs text-[var(--color-anthracite-500)] font-medium">Evidence</span>
                    </div>
                    <Button variant="ghost" size="icon" className="shrink-0 text-[var(--color-anthracite-400)]">
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </Button>
                  </div>
                </div>
                
                {isExpanded && (
                  <div className="bg-[var(--bg-surface-hover)] border-t border-[var(--border-surface)] p-6 animate-in slide-in-from-top-2 duration-200">
                    <h4 className="text-sm font-semibold text-[var(--color-anthracite-500)] uppercase tracking-wider mb-3 flex items-center gap-2">
                      <FileText className="w-4 h-4" /> Supporting Evidence
                    </h4>
                    {claim.evidence ? (
                      <div className="bg-[var(--background)] p-4 rounded-xl border border-[var(--border-surface)] shadow-inner">
                        <p className="text-[var(--foreground)] leading-relaxed italic border-l-4 border-[var(--color-lila-500)] pl-4">
                          "{claim.evidence}"
                        </p>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-[var(--color-anthracite-400)] text-sm italic p-4 bg-[var(--background)] rounded-xl border border-[var(--border-surface)] border-dashed">
                        <AlertCircle className="w-4 h-4" />
                        No explicit supporting evidence found in source documents.
                      </div>
                    )}
                    
                    <div className="mt-6 flex justify-end gap-3">
                      <Button variant="outline" size="sm">Request More Evidence</Button>
                      <Button variant="default" size="sm">Verify with QA</Button>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
