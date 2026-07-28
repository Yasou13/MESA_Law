'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useGetDraftApiV1DraftStudioDraftsDraftIdGet, useUpdateDraftApiV1DraftStudioDraftsDraftIdPut, useApproveDraft } from '@/api/endpoints/draft-studio/draft-studio'
import { ArrowLeft, Save, Loader2, CheckCircle } from 'lucide-react'
import Link from 'next/link'
import { toast } from 'react-hot-toast'

export default function DraftEditorPage() {
  const params = useParams()
  const router = useRouter()
  const draftId = params.id as string

  const { data: draftRes, isLoading } = useGetDraftApiV1DraftStudioDraftsDraftIdGet(draftId)
  const { mutate: updateDraft, isPending: isSaving } = useUpdateDraftApiV1DraftStudioDraftsDraftIdPut()
  const { mutate: approveDraft, isPending: isApproving } = useApproveDraft()

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  useEffect(() => {
    if (draftRes?.data) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTitle((draftRes?.data as any)?.title || '')
      setContent((draftRes?.data as any)?.content || '')
    }
  }, [draftRes?.data])

  const handleSave = () => {
    updateDraft({ 
      draftId, 
      data: { title, content, expected_version: (draftRes?.data as any)?.version }
    }, {
      onSuccess: () => {
        toast.success('Draft saved successfully')
      },
      onError: (err: any) => {
        toast.error(`Save failed: ${err.response?.data?.detail || 'Unknown error'}`)
      }
    })
  }

  const handleApprove = () => {
    approveDraft({ draftId }, {
      onSuccess: () => {
        toast.success('Draft approved for external use')
      },
      onError: (err: any) => {
        toast.error(`Approval failed: ${err.response?.data?.detail || 'Unknown error'}`)
      }
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-6xl mx-auto space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/drafts" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <input 
            type="text" 
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-xl font-bold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)] rounded px-2 text-[var(--foreground)]"
            placeholder="Draft Title"
          />
        </div>
        
        <div className="flex items-center gap-2">
          {(draftRes?.data as any)?.status === 'APPROVED_FOR_EXTERNAL_USE' ? (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 text-green-500 rounded-lg text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              Approved
            </div>
          ) : (
            <button 
              onClick={handleApprove}
              disabled={isApproving}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] text-[var(--foreground)] rounded-lg hover:bg-[var(--bg-surface)] transition-colors text-sm font-medium disabled:opacity-50"
            >
              {isApproving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4 text-green-400" />}
              Approve
            </button>
          )}

          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors text-sm font-medium disabled:opacity-50"
          >
            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Draft
          </button>
        </div>
      </div>

      <div className="flex-1 glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden flex flex-col relative">
        <textarea 
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Start typing your draft here..."
          className="flex-1 w-full p-8 bg-transparent border-none focus:outline-none resize-none font-mono text-sm leading-relaxed text-[var(--foreground)]"
        />
        <div className="absolute bottom-2 right-4 text-xs text-zinc-500 font-mono bg-[var(--bg-surface-hover)] px-2 py-1 rounded">
          {content.length} characters | Version {(draftRes?.data as any)?.version}
        </div>
      </div>
    </div>
  )
}
