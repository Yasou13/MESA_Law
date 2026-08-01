'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQueryClient } from '@tanstack/react-query'
import { Briefcase, Check, Edit, Loader2, X } from 'lucide-react'
import { toast } from 'react-hot-toast'

import {
  getListReviewsQueryKey,
  useApproveReview,
  useCorrectReview,
  useListReviews,
  useRejectReview,
} from '@/api/endpoints/reviews/reviews'
import type { ReviewItemResponse, ReviewState } from '@/api/models'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { StatusBadge } from '@/components/ui/status-badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ApiError } from '@/lib/api/client'

type ReviewTab = 'PROPOSED' | 'ACCEPTED' | 'REJECTED'

const acceptedStates: ReviewState[] = [
  'APPROVED',
  'CORRECTED',
  'PUBLISHING',
  'PUBLISHED',
  'PUBLICATION_FAILED',
]

function errorMessage(error: ApiError): string {
  return error.referenceId
    ? `${error.message} (reference: ${error.referenceId})`
    : error.message
}

export default function GlobalReviewsPage() {
  const queryClient = useQueryClient()
  const [editingReview, setEditingReview] = useState<ReviewItemResponse | null>(null)
  const [editContent, setEditContent] = useState('')
  const [reason, setReason] = useState('')
  const [activeTab, setActiveTab] = useState<ReviewTab>('PROPOSED')
  const { data: reviews = [], isLoading } = useListReviews()

  const filteredReviews = reviews.filter((review) => {
    if (activeTab === 'PROPOSED') return review.status === 'PROPOSED'
    if (activeTab === 'ACCEPTED') return acceptedStates.includes(review.status)
    return review.status === 'REJECTED'
  })

  const invalidateReviews = () =>
    queryClient.invalidateQueries({ queryKey: getListReviewsQueryKey() })
  const closeEditor = () => {
    setEditingReview(null)
    setEditContent('')
    setReason('')
  }

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
        closeEditor()
        await invalidateReviews()
      },
      onError: (error) => toast.error(errorMessage(error)),
    },
  })

  const openEditor = (review: ReviewItemResponse) => {
    setEditingReview(review)
    setEditContent(JSON.stringify(review.corrected_content ?? review.proposed_content, null, 2))
    setReason('')
  }

  const approve = (review: ReviewItemResponse) =>
    approveMutation.mutate({
      reviewId: review.id,
      data: { expected_version: review.version_id },
    })

  const reject = (review: ReviewItemResponse) => {
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

  const saveCorrection = () => {
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

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6 lg:p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Review Center</h1>
        <p className="mt-1 text-[var(--color-anthracite-500)]">
          Human review is required before a suggested assertion enters the canonical record.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as ReviewTab)}>
        <TabsList className="mb-6">
          <TabsTrigger value="PROPOSED">Proposed</TabsTrigger>
          <TabsTrigger value="ACCEPTED">Approved / publishing</TabsTrigger>
          <TabsTrigger value="REJECTED">Rejected</TabsTrigger>
        </TabsList>

        <div className="glass-card overflow-hidden rounded-xl border border-[var(--border-surface)]">
          {isLoading ? (
            <div className="flex h-64 flex-col items-center justify-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--color-lila-500)]" />
              <p className="text-[var(--color-anthracite-500)]">Loading reviews…</p>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="m-4 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--border-surface)] py-24">
              <Check className="mb-4 h-8 w-8 text-[var(--color-anthracite-400)]" />
              <h3 className="text-xl font-bold text-[var(--foreground)]">No reviews in this state</h3>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-[var(--bg-surface-hover)]">
                <TableRow>
                  <TableHead>Matter</TableHead>
                  <TableHead>Review type</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReviews.map((review) => (
                  <TableRow key={review.id}>
                    <TableCell className="font-medium">
                      <Link
                        href={`/matters/${review.matter_id}`}
                        className="flex items-center gap-2 hover:text-[var(--color-lila-500)] hover:underline"
                      >
                        <Briefcase className="h-4 w-4 text-[var(--color-anthracite-400)]" />
                        Matter {review.matter_id.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell>{review.entity_type}</TableCell>
                    <TableCell className="font-mono text-sm">{review.version_id}</TableCell>
                    <TableCell>
                      <StatusBadge
                        status={
                          review.status === 'PROPOSED'
                            ? 'review-required'
                            : review.status === 'REJECTED' || review.status === 'PUBLICATION_FAILED'
                              ? 'error'
                              : 'success'
                        }
                        label={review.status}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {review.status === 'PROPOSED' ? (
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => approve(review)}
                            disabled={approveMutation.isPending}
                            title="Approve"
                          >
                            <Check className="h-4 w-4 text-green-500" />
                          </Button>
                          <Button variant="ghost" size="icon-sm" onClick={() => openEditor(review)} title="Correct">
                            <Edit className="h-4 w-4 text-blue-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => reject(review)}
                            disabled={rejectMutation.isPending}
                            title="Reject"
                          >
                            <X className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={() => openEditor(review)}>
                          View details
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </Tabs>

      <Dialog open={editingReview !== null} onOpenChange={(open) => !open && closeEditor()}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingReview?.status === 'PROPOSED' ? 'Correct assertion' : 'Assertion details'}</DialogTitle>
            <DialogDescription>
              {editingReview?.entity_type} · version {editingReview?.version_id}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <textarea
              aria-label="Assertion JSON"
              readOnly={editingReview?.status !== 'PROPOSED'}
              className="min-h-72 w-full rounded-md border border-[var(--border-surface)] bg-[var(--bg-surface)] p-4 font-mono text-sm text-[var(--foreground)]"
              value={editContent}
              onChange={(event) => setEditContent(event.target.value)}
            />
            {editingReview?.status === 'PROPOSED' && (
              <input
                aria-label="Correction reason"
                className="w-full rounded-md border border-[var(--border-surface)] bg-[var(--bg-surface)] px-3 py-2 text-[var(--foreground)]"
                placeholder="Correction reason (required)"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            )}
            {editingReview?.decision_reason && (
              <p className="text-sm text-[var(--color-anthracite-500)]">
                Decision reason: {editingReview.decision_reason}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeEditor}>Close</Button>
            {editingReview?.status === 'PROPOSED' && (
              <Button onClick={saveCorrection} disabled={correctMutation.isPending}>
                {correctMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save & approve
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
