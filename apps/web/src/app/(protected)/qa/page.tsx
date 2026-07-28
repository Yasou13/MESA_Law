'use client'

import { useState } from 'react'
import { 
  useListDraftReviewsApiV1ReviewsGet, 
  useApproveReviewApiV1ReviewsReviewIdApprovePost, 
  useRejectReviewApiV1ReviewsReviewIdRejectPost 
} from '@/api/endpoints/reviews/reviews'
import { useSystemDependenciesApiV1SystemDependenciesGet } from '@/api/endpoints/system/system'
import { Check, X, AlertTriangle, FileText } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { useQueryClient } from '@tanstack/react-query'

export default function QAPage() {
  const queryClient = useQueryClient()
  const { data: response, isLoading, isError, refetch } = useListDraftReviewsApiV1ReviewsGet()
  const { mutate: approveMutate, isPending: isApproving } = useApproveReviewApiV1ReviewsReviewIdApprovePost()
  const { mutate: rejectMutate, isPending: isRejecting } = useRejectReviewApiV1ReviewsReviewIdRejectPost()
  
  const { data: depsRes } = useSystemDependenciesApiV1SystemDependenciesGet()
  const isMockAdapter = (depsRes?.data as any)?.intelligence_adapter === 'mock'

  const reviews = (response?.data as any[]) || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Failed to load reviews</h2>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-[var(--color-anthracite-700)] text-white rounded-lg hover:bg-[var(--color-anthracite-600)]"
        >
          Retry
        </button>
      </div>
    )
  }

  const handleApprove = (id: string) => {
    approveMutate({ reviewId: id }, {
      onSuccess: () => {
        toast.success('Review approved successfully')
        // Invalidate to refresh the list
        queryClient.invalidateQueries({ queryKey: ['/api/v1/reviews'] })
      }
    })
  }

  const handleReject = (id: string) => {
    rejectMutate({ reviewId: id }, {
      onSuccess: () => {
        toast.success('Review rejected')
        queryClient.invalidateQueries({ queryKey: ['/api/v1/reviews'] })
      }
    })
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {isMockAdapter && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-amber-500">Degraded Intelligence Mode</h3>
            <p className="text-xs text-amber-500/80 mt-1">
              MESA Core intelligence is running in MOCK mode. AI answers will be simulated.
            </p>
          </div>
        </div>
      )}
      
      <div>
        <h1 className="text-2xl font-bold tracking-tight">QA Review Center</h1>
        <p className="text-zinc-400">Review and approve extracted entities and summaries.</p>
      </div>

      <div className="space-y-4">
        {reviews.length === 0 ? (
          <div className="glass-card rounded-xl p-12 text-center text-zinc-400">
            <Check className="w-12 h-12 text-green-400/50 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">All caught up!</h3>
            <p>There are no pending items requiring your review.</p>
          </div>
        ) : (
          reviews.map((review: any) => (
            <div key={review.id} className="glass-card rounded-xl p-6">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[var(--bg-surface-hover)] flex items-center justify-center border border-[var(--border-surface)]">
                    <FileText className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg capitalize">{review.entity_type}</h3>
                    <p className="text-xs text-zinc-500 font-mono mt-0.5">Matter: {review.matter_id}</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleReject(review.id)}
                    disabled={isApproving || isRejecting}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <X className="w-4 h-4" /> Reject
                  </button>
                  <button 
                    onClick={() => handleApprove(review.id)}
                    disabled={isApproving || isRejecting}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-500 hover:bg-green-500/20 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <Check className="w-4 h-4" /> Approve
                  </button>
                </div>
              </div>
              
              <div className="bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg p-4">
                <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">Proposed Content</h4>
                <pre className="text-sm text-[var(--foreground)] whitespace-pre-wrap font-mono">
                  {JSON.stringify(review.proposed_content, null, 2)}
                </pre>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
