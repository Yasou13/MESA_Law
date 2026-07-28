'use client'

import { use } from 'react'
import { ArrowLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { DraftStudioShell } from '@/features/drafts/components/DraftStudioShell'
import { useGetDraftApiV1DraftStudioDraftsDraftIdGet as useGetDraft } from '@/api/endpoints/draft-studio/draft-studio'

export default function DraftStudioPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const draftId = resolvedParams.id
  
  const { data: draft, isLoading, isError } = useGetDraft(draftId)
  
  if (isLoading) {
    return <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-[var(--background)]"><Loader2 className="w-8 h-8 text-[var(--color-lila-500)] animate-spin" /></div>
  }
  
  if (isError || !draft) {
    return <div className="flex h-[calc(100vh-4rem)] items-center justify-center bg-[var(--background)] text-red-500 font-medium">Failed to load draft</div>
  }

  const matterId = (draft as any).matter_id;

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden w-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-4 border-b border-[var(--border-surface)] flex items-center justify-between">
          <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Matter
          </Link>
        </div>

        <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[var(--bg-surface-hover)]">
          <div className="max-w-7xl mx-auto w-full h-[850px] shadow-sm rounded-xl overflow-hidden border border-[var(--border-surface)] flex flex-col">
            <DraftStudioShell matterId={matterId} />
          </div>
        </div>
      </div>
    </div>
  )
}
