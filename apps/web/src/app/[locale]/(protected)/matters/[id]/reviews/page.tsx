'use client'

import { use } from 'react'

import { ReviewWorkspace } from '@/features/reviews/components/ReviewWorkspace'

export default function MatterReviewsPage({ params }: { params: Promise<{ id: string }> }) {
  return <ReviewWorkspace matterId={use(params).id} />
}
