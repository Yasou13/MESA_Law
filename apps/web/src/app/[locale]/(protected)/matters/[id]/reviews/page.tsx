'use client'

import { use, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Check, Edit, Loader2, X } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'react-hot-toast'

import {
  getListReviewsQueryKey,
  useApproveReview,
  useCorrectReview,
  useListReviews,
  useRejectReview,
} from '@/api/endpoints/reviews/reviews'
import type { ReviewItemResponse } from '@/api/models'
import { ApiError } from '@/lib/api/client'

function errorMessage(error: ApiError): string {
  return error.referenceId
    ? `${error.message} (reference: ${error.referenceId})`
    : error.message
}

export default function MatterReviewsPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const queryClient = useQueryClient()
  const queryParams = { matter_id: matterId }
  const [editingReview, setEditingReview] = useState<ReviewItemResponse | null>(null)
  const [editContent, setEditContent] = useState('')
  const [reason, setReason] = useState('')

  const { data: reviews = [], isLoading } = useListReviews(queryParams)
  const invalidateReviews = () =>
    queryClient.invalidateQueries({ queryKey: getListReviewsQueryKey(queryParams) })

  const approveMutation = useApproveReview<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success('Review approved and queued for publication')
        await invalidateReviews()
      },
      onError: (error) => toast.error(errorMessage(error)),
    },
  })
  const rejectMutation = useRejectReview<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success('Review rejected')
        await invalidateReviews()
      },
      onError: (error) => toast.error(errorMessage(error)),
    },
  })
  const correctMutation = useCorrectReview<ApiError>({
    mutation: {
      onSuccess: async () => {
        toast.success('Correction approved and queued for publication')
        setEditingReview(null)
        setReason('')
        await invalidateReviews()
      },
      onError: (error) => toast.error(errorMessage(error)),
    },
  })

  const handleApprove = (review: ReviewItemResponse) =>
    approveMutation.mutate({
      reviewId: review.id,
      data: { expected_version: review.version_id },
    })

  const handleReject = (review: ReviewItemResponse) => {
    const rejectionReason = window.prompt('Rejection reason (required):')?.trim()
    if (!rejectionReason || rejectionReason.length < 3) {
      toast.error('A rejection reason of at least 3 characters is required')
      return
    }
    rejectMutation.mutate({
      reviewId: review.id,
      data: { expected_version: review.version_id, reason: rejectionReason },
    })
  }

  const handleEdit = (review: ReviewItemResponse) => {
    setEditingReview(review)
    setEditContent(JSON.stringify(review.proposed_content, null, 2))
    setReason('')
  }

  const handleSaveCorrection = () => {
    if (!editingReview || reason.trim().length < 3) {
      toast.error('A correction reason of at least 3 characters is required')
      return
    }
    try {
      const correctedContent = JSON.parse(editContent) as Record<string, unknown>
      correctMutation.mutate({
        reviewId: editingReview.id,
        data: {
          corrected_content: correctedContent,
          expected_version: editingReview.version_id,
          reason: reason.trim(),
        },
      })
    } catch {
      toast.error('Correction must be valid JSON')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--color-lila-500)]" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl p-8 lg:p-12">
      <div className="mb-12">
        <h1 className="mb-2 text-4xl font-bold tracking-tight text-[var(--foreground)]">
          Matter Review Center
        </h1>
        <p className="text-[var(--color-anthracite-400)]">
          Only approved or corrected assertions can enter the canonical record and MESA publication queue.
        </p>
      </div>

      {reviews.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-[var(--color-anthracite-500)]" />
          <h3 className="text-xl font-medium text-[var(--foreground)]">All caught up</h3>
          <p className="text-[var(--color-anthracite-400)]">No reviews exist for this matter.</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {reviews.map((review) => (
            <motion.div
              key={review.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card flex flex-col gap-6 rounded-2xl border border-[var(--border-surface)] p-6 md:flex-row"
            >
              <div className="min-w-0 flex-1">
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <span className="rounded-full bg-[var(--color-lila-500)]/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[var(--color-lila-300)]">
                    {review.entity_type}
                  </span>
                  <span className="text-xs font-medium text-[var(--color-anthracite-400)]">
                    {review.status} · version {review.version_id}
                  </span>
                </div>

                {editingReview?.id === review.id ? (
                  <div className="space-y-4">
                    <textarea
                      aria-label="Corrected assertion JSON"
                      className="min-h-52 w-full rounded-xl border border-[var(--border-surface)] bg-[var(--bg-surface)] p-4 font-mono text-sm text-[var(--foreground)]"
                      value={editContent}
                      onChange={(event) => setEditContent(event.target.value)}
                    />
                    <input
                      aria-label="Correction reason"
                      className="w-full rounded-xl border border-[var(--border-surface)] bg-[var(--bg-surface)] p-3 text-sm text-[var(--foreground)]"
                      placeholder="Correction reason (required)"
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                    />
                    <div className="flex gap-3">
                      <button
                        onClick={handleSaveCorrection}
                        className="btn-primary"
                        disabled={correctMutation.isPending}
                      >
                        {correctMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save & approve'}
                      </button>
                      <button onClick={() => setEditingReview(null)} className="btn-secondary">
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <pre className="overflow-x-auto rounded-xl border border-[var(--border-surface)] bg-[var(--bg-surface)] p-4 font-mono text-sm text-[var(--color-anthracite-300)]">
                    {JSON.stringify(review.corrected_content ?? review.proposed_content, null, 2)}
                  </pre>
                )}
                {review.decision_reason && (
                  <p className="mt-3 text-sm text-[var(--color-anthracite-400)]">
                    Decision reason: {review.decision_reason}
                  </p>
                )}
              </div>

              {review.status === 'PROPOSED' && editingReview?.id !== review.id && (
                <div className="flex min-w-36 justify-start gap-3 md:flex-col">
                  <button
                    onClick={() => handleApprove(review)}
                    disabled={approveMutation.isPending}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-green-500/20 bg-green-500/10 px-4 py-3 font-medium text-green-400 transition-colors hover:bg-green-500/20"
                  >
                    <Check className="h-4 w-4" /> Approve
                  </button>
                  <button
                    onClick={() => handleEdit(review)}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-3 font-medium text-blue-400 transition-colors hover:bg-blue-500/20"
                  >
                    <Edit className="h-4 w-4" /> Correct
                  </button>
                  <button
                    onClick={() => handleReject(review)}
                    disabled={rejectMutation.isPending}
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 font-medium text-red-400 transition-colors hover:bg-red-500/20"
                  >
                    <X className="h-4 w-4" /> Reject
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
