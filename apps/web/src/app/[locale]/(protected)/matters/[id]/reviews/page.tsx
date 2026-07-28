'use client'

import { useQueryClient } from '@tanstack/react-query'
import { useState, use } from 'react'
import { Check, X, Edit, Loader2, AlertCircle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'
import { 
  useListDraftReviewsApiV1ReviewsGet,
  useApproveReviewApiV1ReviewsReviewIdApprovePost,
  useRejectReviewApiV1ReviewsReviewIdRejectPost,
  useCorrectReviewApiV1ReviewsReviewIdCorrectPost
} from '@/api/endpoints/reviews/reviews'

export default function MatterReviewsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState<string>("")

  const { data: reviewsResponse, isLoading } = useListDraftReviewsApiV1ReviewsGet({ matter_id: matterId })
  const reviews = Array.isArray(reviewsResponse) ? reviewsResponse : []

  const approveMutation = useApproveReviewApiV1ReviewsReviewIdApprovePost({
    mutation: {
      onSuccess: () => {
        toast.success("Review approved successfully")
        queryClient.invalidateQueries({ queryKey: ['/api/v1/reviews'] })
      },
      onError: () => toast.error("Failed to approve review")
    }
  })

  const rejectMutation = useRejectReviewApiV1ReviewsReviewIdRejectPost({
    mutation: {
      onSuccess: () => {
        toast.success("Review rejected")
        queryClient.invalidateQueries({ queryKey: ['/api/v1/reviews'] })
      },
      onError: () => toast.error("Failed to reject review")
    }
  })

  const correctMutation = useCorrectReviewApiV1ReviewsReviewIdCorrectPost({
    mutation: {
      onSuccess: () => {
        toast.success("Review corrected and approved")
        setEditingId(null)
        queryClient.invalidateQueries({ queryKey: ['/api/v1/reviews'] })
      },
      onError: () => toast.error("Failed to correct review")
    }
  })

  const handleApprove = (id: string) => approveMutation.mutate({ reviewId: id })
  const handleReject = (id: string) => rejectMutation.mutate({ reviewId: id })
  
  const handleEdit = (id: string, content: any) => {
    setEditingId(id)
    setEditContent(JSON.stringify(content, null, 2))
  }

  const handleSaveCorrection = (id: string) => {
    try {
      const parsed = JSON.parse(editContent)
      correctMutation.mutate({ reviewId: id, data: { corrected_content: parsed } })
    } catch (e) {
      toast.error("Invalid JSON format for correction")
    }
  }

  if (isLoading) {
    return <div className="p-12 flex justify-center"><Loader2 className="animate-spin w-8 h-8 text-[var(--color-lila-500)]" /></div>
  }

  return (
    <div className="max-w-7xl mx-auto p-8 lg:p-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold tracking-tight text-[var(--foreground)] mb-2">Matter Review Center</h1>
        <p className="text-[var(--color-anthracite-400)]">Review pending items specifically for this matter.</p>
      </div>

      {reviews.length === 0 ? (
        <div className="glass-card p-12 text-center rounded-2xl">
          <AlertCircle className="w-12 h-12 text-[var(--color-anthracite-500)] mx-auto mb-4" />
          <h3 className="text-xl font-medium text-[var(--foreground)]">All Caught Up</h3>
          <p className="text-[var(--color-anthracite-400)]">No pending reviews require your attention in this matter.</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {reviews.map((review: any) => (
            <motion.div 
              key={review.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-2xl p-6 border border-[var(--border-surface)] flex flex-col md:flex-row gap-6"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <span className="px-3 py-1 text-xs font-semibold uppercase tracking-wider bg-[var(--color-lila-500)]/20 text-[var(--color-lila-300)] rounded-full">
                    {review.entity_type}
                  </span>
                </div>
                
                {editingId === review.id ? (
                  <div className="space-y-4">
                    <textarea 
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl p-4 text-[var(--foreground)] font-mono text-sm min-h-[200px]"
                      value={editContent}
                      onChange={e => setEditContent(e.target.value)}
                    />
                    <div className="flex gap-3">
                      <button 
                        onClick={() => handleSaveCorrection(review.id)}
                        className="btn-primary"
                        disabled={correctMutation.isPending}
                      >
                        {correctMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save & Approve"}
                      </button>
                      <button 
                        onClick={() => setEditingId(null)}
                        className="btn-secondary"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <pre className="bg-[var(--bg-surface)] p-4 rounded-xl text-sm font-mono text-[var(--color-anthracite-300)] overflow-x-auto border border-[var(--border-surface)]">
                    {JSON.stringify(review.proposed_content, null, 2)}
                  </pre>
                )}
              </div>
              
              {!editingId && (
                <div className="flex md:flex-col gap-3 justify-start min-w-[140px]">
                  <button 
                    onClick={() => handleApprove(review.id)}
                    disabled={approveMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 rounded-xl px-4 py-3 font-medium transition-colors"
                  >
                    <Check className="w-4 h-4" /> Approve
                  </button>
                  <button 
                    onClick={() => handleEdit(review.id, review.proposed_content)}
                    className="flex-1 flex items-center justify-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-xl px-4 py-3 font-medium transition-colors"
                  >
                    <Edit className="w-4 h-4" /> Correct
                  </button>
                  <button 
                    onClick={() => handleReject(review.id)}
                    disabled={rejectMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl px-4 py-3 font-medium transition-colors"
                  >
                    <X className="w-4 h-4" /> Reject
                  </button>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
