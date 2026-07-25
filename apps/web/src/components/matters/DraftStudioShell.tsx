'use client'

import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'react-hot-toast'
import { FileEdit, Plus, Save, Download, Loader2, Clock, Check, RefreshCw } from 'lucide-react'

type DraftListItem = {
  id: string
  title: string
  version: number
  updated_at?: string
}

type DraftDetail = {
  id: string
  matter_id: string
  title: string
  content?: string
  version: number
  updated_at?: string
}

export function DraftStudioShell({ matterId }: { matterId: string }) {
  const queryClient = useQueryClient()
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [currentVersion, setCurrentVersion] = useState(1)
  const [isDirty, setIsDirty] = useState(false)

  const { data: drafts, isLoading: isLoadingList } = useQuery<DraftListItem[]>({
    queryKey: ['drafts', matterId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/draft-studio/drafts/matter/${matterId}`)
      return res.data
    }
  })

  const { data: activeDraft, isLoading: isLoadingDetail } = useQuery<DraftDetail>({
    queryKey: ['draft', activeDraftId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/draft-studio/drafts/${activeDraftId}`)
      return res.data
    },
    enabled: !!activeDraftId
  })

  useEffect(() => {
    if (activeDraft) {
      setTitle(activeDraft.title)
      setContent(activeDraft.content || '')
      setCurrentVersion(activeDraft.version)
      setIsDirty(false)
    }
  }, [activeDraft])

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await axios.post('/api/v1/draft-studio/drafts', {
        matter_id: matterId,
        title: 'New Legal Draft',
        content: '# New Legal Document\n\nEnter clauses and terms here...'
      })
      return res.data
    },
    onSuccess: (data) => {
      toast.success('New draft created')
      queryClient.invalidateQueries({ queryKey: ['drafts', matterId] })
      setActiveDraftId(data.id)
    },
    onError: () => toast.error('Failed to create draft')
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!activeDraftId) return
      const res = await axios.put(`/api/v1/draft-studio/drafts/${activeDraftId}`, {
        title,
        content,
        expected_version: currentVersion
      })
      return res.data
    },
    onSuccess: (data) => {
      toast.success(`Draft saved (v${data.version})`)
      setCurrentVersion(data.version)
      setIsDirty(false)
      queryClient.invalidateQueries({ queryKey: ['drafts', matterId] })
      queryClient.invalidateQueries({ queryKey: ['draft', activeDraftId] })
    },
    onError: (error: any) => {
      if (error.response?.status === 409) {
        toast.error('Version conflict! Someone else modified this draft.')
      } else {
        toast.error('Failed to save draft')
      }
    }
  })

  const exportMutation = useMutation({
    mutationFn: async (format: 'pdf' | 'docx') => {
      if (!activeDraftId) return
      const res = await axios.post(`/api/v1/draft-studio/drafts/${activeDraftId}/export`, { format })
      return res.data
    },
    onSuccess: (data) => {
      toast.success(`Export job queued (${data.format.toUpperCase()})`)
    },
    onError: () => toast.error('Export request failed')
  })

  return (
    <div className="flex gap-6 min-h-[500px] border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/40">
      {/* Sidebar List */}
      <div className="w-64 border-r border-zinc-800 p-4 flex flex-col bg-zinc-900/80">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-zinc-200 flex items-center gap-2">
            <FileEdit className="w-4 h-4 text-blue-400" />
            Drafts
          </h3>
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="p-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50"
            title="New Draft"
          >
            {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          </button>
        </div>

        {isLoadingList ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
          </div>
        ) : drafts && drafts.length > 0 ? (
          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {drafts.map((d) => (
              <button
                key={d.id}
                onClick={() => setActiveDraftId(d.id)}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors flex flex-col gap-1 ${
                  activeDraftId === d.id
                    ? 'bg-blue-600/20 border border-blue-500/30 text-white'
                    : 'hover:bg-zinc-800/60 text-zinc-300'
                }`}
              >
                <div className="font-medium truncate">{d.title}</div>
                <div className="flex items-center justify-between text-xs text-zinc-400">
                  <span className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300 font-mono">v{d.version}</span>
                  {d.updated_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(d.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 text-zinc-500 text-sm">
            <FileEdit className="w-8 h-8 mb-2 stroke-1" />
            <p>No drafts created yet.</p>
            <p className="text-xs mt-1 text-zinc-600">Click + to start writing.</p>
          </div>
        )}
      </div>

      {/* Editor Main Area */}
      <div className="flex-1 p-6 flex flex-col">
        {!activeDraftId ? (
          <div className="flex-1 flex flex-col items-center justify-center text-zinc-500">
            <FileEdit className="w-12 h-12 mb-3 stroke-1 text-zinc-600" />
            <h4 className="text-lg font-medium text-zinc-400">Select or Create a Draft</h4>
            <p className="text-sm mt-1">Choose a draft from the left sidebar to start editing.</p>
          </div>
        ) : isLoadingDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        ) : (
          <>
            {/* Header / Actions */}
            <div className="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-zinc-800">
              <input
                type="text"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value)
                  setIsDirty(true)
                }}
                placeholder="Draft Title..."
                className="bg-transparent text-xl font-semibold text-zinc-100 focus:outline-none focus:ring-1 focus:ring-blue-500/50 rounded px-2 py-1 flex-1 border border-transparent hover:border-zinc-800"
              />
              
              <div className="flex items-center gap-2">
                <span className="text-xs bg-zinc-800 text-zinc-300 font-mono px-2 py-1 rounded-md border border-zinc-700/50">
                  Version {currentVersion}
                </span>

                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={!isDirty || saveMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save
                </button>

                <div className="h-4 w-[1px] bg-zinc-800 mx-1" />

                <button
                  onClick={() => exportMutation.mutate('pdf')}
                  disabled={exportMutation.isPending || isDirty}
                  title={isDirty ? 'Save changes before exporting' : 'Queue PDF Export'}
                  className="flex items-center gap-1 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-200 text-sm rounded-lg transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-red-400" />
                  PDF
                </button>

                <button
                  onClick={() => exportMutation.mutate('docx')}
                  disabled={exportMutation.isPending || isDirty}
                  title={isDirty ? 'Save changes before exporting' : 'Queue DOCX Export'}
                  className="flex items-center gap-1 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-200 text-sm rounded-lg transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-blue-400" />
                  DOCX
                </button>
              </div>
            </div>

            {/* Content Editor */}
            <div className="flex-1 flex flex-col">
              <textarea
                value={content}
                onChange={(e) => {
                  setContent(e.target.value)
                  setIsDirty(true)
                }}
                placeholder="Write or edit clauses, legal arguments, and contractual provisions here..."
                className="flex-1 w-full bg-zinc-950/60 border border-zinc-800/80 rounded-xl p-4 text-zinc-200 font-mono text-sm leading-relaxed resize-none focus:outline-none focus:border-blue-500/50 transition-colors"
              />
              
              <div className="flex justify-between items-center mt-3 text-xs text-zinc-500 px-1">
                <span>{isDirty ? '⚠️ Unsaved changes' : '✓ All changes saved'}</span>
                <span>{content.length} characters</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
