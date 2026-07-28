'use client'

import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Check, X, Edit, Loader2, AlertCircle, FileText, Briefcase } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { 
  useListDraftReviewsApiV1ReviewsGet,
  getListDraftReviewsApiV1ReviewsGetQueryKey,
  useApproveReviewApiV1ReviewsReviewIdApprovePost,
  useRejectReviewApiV1ReviewsReviewIdRejectPost,
  useCorrectReviewApiV1ReviewsReviewIdCorrectPost
} from '@/api/endpoints/reviews/reviews'
import { useListMatterParties } from '@/api/endpoints/default/default'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import Link from 'next/link'

export default function GlobalReviewsPage() {
  const queryClient = useQueryClient()
  const [editingReview, setEditingReview] = useState<any | null>(null)
  const [editData, setEditData] = useState<any>({})
  const [activeTab, setActiveTab] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING')

  const { data: reviewsResponse, isLoading, refetch } = useListDraftReviewsApiV1ReviewsGet()
  const reviews = Array.isArray(reviewsResponse) ? reviewsResponse : []

  const filteredReviews = reviews.filter(r => {
    if (activeTab === 'PENDING') return r.status === 'PENDING' || r.status === 'IN_REVIEW'
    if (activeTab === 'APPROVED') return r.status === 'APPROVED_PENDING_PUBLICATION' || r.status === 'PUBLISHED'
    if (activeTab === 'REJECTED') return r.status === 'REJECTED' || r.status === 'DUPLICATE'
    return false
  })

  const approveMutation = useApproveReviewApiV1ReviewsReviewIdApprovePost({
    mutation: {
      onSuccess: () => {
        toast.success("Review approved successfully")
        queryClient.invalidateQueries({ queryKey: getListDraftReviewsApiV1ReviewsGetQueryKey() })
      },
      onError: () => toast.error("Failed to approve review")
    }
  })

  const rejectMutation = useRejectReviewApiV1ReviewsReviewIdRejectPost({
    mutation: {
      onSuccess: () => {
        toast.success("Review rejected")
        queryClient.invalidateQueries({ queryKey: getListDraftReviewsApiV1ReviewsGetQueryKey() })
      },
      onError: () => toast.error("Failed to reject review")
    }
  })

  const correctMutation = useCorrectReviewApiV1ReviewsReviewIdCorrectPost({
    mutation: {
      onSuccess: () => {
        toast.success("Review corrected and approved")
        setEditingReview(null)
        queryClient.invalidateQueries({ queryKey: getListDraftReviewsApiV1ReviewsGetQueryKey() })
      },
      onError: () => toast.error("Failed to correct review")
    }
  })

  const handleApprove = (id: string) => approveMutation.mutate({ reviewId: id })
  const handleReject = (id: string) => rejectMutation.mutate({ reviewId: id })
  
  const handleEdit = (review: any) => {
    setEditingReview(review)
    setEditData(review.proposed_content || {})
  }

  const handleSaveCorrection = () => {
    if (!editingReview) return
    correctMutation.mutate({ reviewId: editingReview.id, data: { corrected_content: editData } })
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Review Center</h1>
        <p className="text-[var(--color-anthracite-500)] mt-1">Review pending AI extractions, claims, and timeline events across all matters.</p>
      </div>

      <Tabs value={activeTab} onValueChange={(val: any) => setActiveTab(val)} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="PENDING" className="relative">
            Pending
            {reviews.filter(r => r.status === 'PENDING' || r.status === 'IN_REVIEW').length > 0 && (
              <span className="ml-2 w-2 h-2 rounded-full bg-[var(--color-semantic-info)]"></span>
            )}
          </TabsTrigger>
          <TabsTrigger value="APPROVED">Approved</TabsTrigger>
          <TabsTrigger value="REJECTED">Rejected</TabsTrigger>
        </TabsList>
        
        <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
              <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading reviews...</p>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
              <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
                <Check className="w-8 h-8 text-[var(--color-anthracite-400)]" />
              </div>
              <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">All Caught Up</h3>
              <p className="text-[var(--color-anthracite-500)]">No {activeTab} reviews found.</p>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-[var(--bg-surface-hover)]">
                <TableRow>
                  <TableHead>Matter</TableHead>
                  <TableHead>Review Type</TableHead>
                  <TableHead>Target ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReviews.map((review: any) => (
                  <TableRow key={review.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                    <TableCell className="font-medium">
                      <Link href={`/matters/${review.matter_id}`} className="hover:text-[var(--color-lila-500)] hover:underline flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                        Matter {review.matter_id.substring(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-[var(--color-lila-500)]/10 text-[var(--color-lila-600)] dark:text-[var(--color-lila-400)] rounded-md border border-[var(--color-lila-500)]/20">
                        {review.entity_type}
                      </span>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-[var(--color-anthracite-500)]">
                      {review.entity_id.substring(0, 8)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge 
                        status={review.status === 'pending' ? 'review-required' : review.status === 'approved' ? 'success' : 'error'} 
                        label={review.status.toUpperCase()} 
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {review.status === 'pending' ? (
                        <div className="flex items-center justify-end gap-2">
                          <Button 
                            variant="ghost" 
                            size="icon-sm" 
                            onClick={() => handleApprove(review.id)}
                            disabled={approveMutation.isPending}
                            title="Approve"
                            className="text-green-500 hover:text-green-600 hover:bg-green-500/10"
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon-sm" 
                            onClick={() => handleEdit(review)}
                            title="Review & Correct"
                            className="text-blue-500 hover:text-blue-600 hover:bg-blue-500/10"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon-sm" 
                            onClick={() => handleReject(review.id)}
                            disabled={rejectMutation.isPending}
                            title="Reject"
                            className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={() => handleEdit(review)}>
                          View Details
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

      <Dialog open={!!editingReview} onOpenChange={(open) => !open && setEditingReview(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingReview?.status === 'pending' ? 'Review & Correct Extraction' : 'View Extraction Details'}</DialogTitle>
            <DialogDescription>
              {editingReview?.entity_type} extracted for Matter {editingReview?.matter_id.substring(0, 8)}
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4 space-y-4">
            {editingReview?.entity_type === 'party' && (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Party Name</label>
                  <input
                    type="text"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({...editData, name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Role</label>
                  <input
                    type="text"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                    value={editData.role || ''}
                    onChange={(e) => setEditData({...editData, role: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Type (Organization/Individual)</label>
                  <input
                    type="text"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                    value={editData.type || ''}
                    onChange={(e) => setEditData({...editData, type: e.target.value})}
                  />
                </div>
              </>
            )}

            {editingReview?.entity_type === 'claim' && (
              <ClaimEditForm 
                matterId={editingReview.matter_id} 
                editData={editData} 
                setEditData={setEditData} 
              />
            )}

            {editingReview?.entity_type === 'deadline' && (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Description</label>
                  <input
                    type="text"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                    value={editData.description || ''}
                    onChange={(e) => setEditData({...editData, description: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Due Date / Calculated Date</label>
                    <input
                      type="text"
                      placeholder="YYYY-MM-DD"
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                      value={editData.due_date || editData.calculated_date || ''}
                      onChange={(e) => setEditData({...editData, due_date: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Trigger Event</label>
                    <input
                      type="text"
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
                      value={editData.trigger_event || ''}
                      onChange={(e) => setEditData({...editData, trigger_event: e.target.value})}
                    />
                  </div>
                </div>
              </>
            )}
            
            {/* Fallback for unknown entity types */}
            {!['party', 'claim', 'deadline'].includes(editingReview?.entity_type) && (
              <div className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-md text-orange-400">
                Custom entity type. Dynamic form not available.
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingReview(null)}>Cancel</Button>
            {editingReview?.status === 'pending' && (
              <Button onClick={handleSaveCorrection} disabled={correctMutation.isPending}>
                {correctMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Save & Approve
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function ClaimEditForm({ matterId, editData, setEditData }: { matterId: string, editData: any, setEditData: any }) {
  const { data: partiesResponse, isLoading } = useListMatterParties(matterId, { query: { enabled: !!matterId } })
  const parties = Array.isArray(partiesResponse) ? partiesResponse : []

  return (
    <>
      <div className="space-y-2">
        <label className="text-sm font-medium">Description</label>
        <textarea
          className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)] min-h-[100px]"
          value={editData.description || ''}
          onChange={(e) => setEditData({...editData, description: e.target.value})}
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center justify-between">
            Claimant Party 
            {isLoading && <Loader2 className="w-3 h-3 animate-spin text-[var(--color-anthracite-500)]" />}
          </label>
          <select
            className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
            value={editData.claimant_party_id || ''}
            onChange={(e) => setEditData({...editData, claimant_party_id: e.target.value})}
          >
            <option value="" disabled>Select Party</option>
            {parties.map((p: any) => (
              <option key={p.id} value={p.id}>{p.name} ({p.role})</option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center justify-between">
            Defendant Party 
            {isLoading && <Loader2 className="w-3 h-3 animate-spin text-[var(--color-anthracite-500)]" />}
          </label>
          <select
            className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-md px-3 py-2 text-[var(--foreground)]"
            value={editData.defendant_party_id || ''}
            onChange={(e) => setEditData({...editData, defendant_party_id: e.target.value})}
          >
            <option value="" disabled>Select Party</option>
            {parties.map((p: any) => (
              <option key={p.id} value={p.id}>{p.name} ({p.role})</option>
            ))}
          </select>
        </div>
      </div>
    </>
  )
}
