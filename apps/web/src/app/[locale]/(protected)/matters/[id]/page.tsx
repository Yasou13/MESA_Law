'use client'

import { useQueryClient } from '@tanstack/react-query'
import { useState, useRef, use } from 'react'
import { FileText, UploadCloud, Loader2, PenTool, LayoutTemplate, Briefcase } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { DocumentViewer } from '@/features/documents/components/DocumentViewer'
import { Timeline } from '@/features/matters/components/Timeline'
import { ClaimsEvidence } from '@/features/matters/components/ClaimsEvidence'
import { ResearchShell } from '@/features/research/components/ResearchShell'
import { QAShell } from '@/features/qa/components/QAShell'
import { DraftStudioShell } from '@/features/drafts/components/DraftStudioShell'
import { MatterContextHeader } from '@/components/layout/MatterContextHeader'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'
import {
  useListMatterDocuments,
  useListClaims,
  useListMatters,
  useCreateUploadIntent,
  useCompleteUpload,
  downloadDocument,
  useRebuildMatterMesa
} from '@/api/endpoints/default/default'
import { useListMatterDraftsApiV1DraftStudioDraftsMatterMatterIdGet, useSaveDraftApiV1DraftStudioDraftsPost } from '@/api/endpoints/draft-studio/draft-studio'

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  const router = useRouter()
  
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { mutateAsync: saveDraft, isPending: isCreatingDraft } = useSaveDraftApiV1DraftStudioDraftsPost()
  const { mutateAsync: rebuildMesa, isPending: isRebuilding } = useRebuildMatterMesa()
  
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'claims' | 'research' | 'drafts'>('overview')
  const [activeDoc, setActiveDoc] = useState<{url: string, title: string} | null>(null)

  // Fetch all matters and find current to pass to MatterContextHeader
  const { data: mattersResponse, isLoading: isLoadingMatters } = useListMatters()
  const matters = Array.isArray(mattersResponse?.data) ? mattersResponse.data : ((mattersResponse?.data as any)?.items || [])
  const currentMatter = matters.find((m: any) => m.id === matterId) || {
    name: 'Loading...',
    status: '...',
    confidentiality_level: '...',
    legal_hold: false,
    ai_processing_policy: '...'
  }

  const { data: documentsResponse, isLoading: isLoadingDocs } = useListMatterDocuments(matterId, {
    query: {
      refetchInterval: (query: any) => {
        const docs = query.state?.data?.data
        if (docs?.some((d: any) => d.status === 'uploading' || d.status === 'scanning' || d.status === 'processing')) {
          return 3000
        }
        return false
      }
    }
  })
  const documents = Array.isArray(documentsResponse?.data) ? documentsResponse.data : []

  const { data: claimsResponse, isLoading: isLoadingClaims } = useListClaims(matterId)
  const claims = Array.isArray(claimsResponse?.data) ? claimsResponse.data : []

  const { data: draftsResponse, isLoading: isLoadingDrafts } = useListMatterDraftsApiV1DraftStudioDraftsMatterMatterIdGet(matterId)
  const drafts = Array.isArray(draftsResponse?.data) ? draftsResponse.data : []

  const uploadIntent = useCreateUploadIntent()
  const completeUpload = useCompleteUpload()

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      const intentRes = await uploadIntent.mutateAsync({
        data: {
          matter_id: matterId,
          filename: file.name,
          mime_type: file.type || 'application/pdf',
          size_bytes: file.size
        }
      })
      const intentData = intentRes.data as any
      const { document_id, presigned_url } = intentData
      
      setUploadProgress(50)
      await fetch(presigned_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/pdf'
        }
      })
      setUploadProgress(90)

      await completeUpload.mutateAsync({ documentId: document_id })
      
      setUploadProgress(100)
      toast.success('Document uploaded successfully')
      queryClient.invalidateQueries({ queryKey: [`/api/v1/documents/matter/${matterId}`] })
    } catch (err: any) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed'
      toast.error(`Upload Failed: ${errorMsg}`)
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleCreateDraft = async () => {
    try {
      const res = await saveDraft({
        data: {
          matter_id: matterId,
          title: 'New Draft',
          content: ''
        }
      })
      toast.success('Draft created')
      router.push(`/drafts/${(res.data as any).id}`)
    } catch (err) {
      toast.error('Failed to create draft')
    }
  }

  const handleRebuildMesa = async () => {
    try {
      const res = await rebuildMesa({ matterId })
      toast.success(`Successfully synced ${(res.data as any).synced_pages} pages to MESA Core`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to sync with MESA Core')
    }
  }

  if (activeDoc) {
    return <DocumentViewer url={activeDoc.url} title={activeDoc.title} onClose={() => setActiveDoc(null)} />
  }

  return (
    <div className="flex flex-col h-full bg-[var(--background)]">
      {/* Top Header */}
      {!isLoadingMatters && currentMatter && (
        <MatterContextHeader 
          matter={{
            name: currentMatter.name || currentMatter.title,
            internal_reference: currentMatter.internal_reference || matterId.substring(0, 8),
            client_name: currentMatter.client_name || 'Client',
            responsible_attorney_name: currentMatter.responsible_attorney_name || 'Partner',
            status: currentMatter.status || 'ACTIVE',
            confidentiality_level: currentMatter.confidentiality_level || 'Strict',
            legal_hold: currentMatter.legal_hold || false,
            ai_processing_policy: currentMatter.ai_processing_policy || 'Standard'
          }} 
        />
      )}

      {/* Tabs Navigation */}
      <div className="bg-[var(--bg-surface)] border-b border-[var(--border-surface)] px-6 py-2">
        <div className="flex items-center gap-1">
          {['overview', 'timeline', 'claims', 'research', 'drafts'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === tab ? 'bg-[var(--bg-surface-hover)] text-[var(--foreground)]' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]'}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto p-6 md:p-8">
        <div className="max-w-7xl mx-auto">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              
              {/* Left Column: Timeline */}
              <div className="lg:col-span-4 space-y-6">
                <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                  <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
                    <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
                      Timeline Overview
                    </h3>
                  </div>
                  <div className="max-h-[600px] overflow-y-auto">
                    <Timeline matterId={matterId} />
                  </div>
                </div>
              </div>
              
              {/* Middle Column: Documents and Drafts */}
              <div className="lg:col-span-5 space-y-6">
                
                {/* Upload Action */}
                <div 
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                  className={`border-2 border-dashed border-[var(--border-surface)] rounded-xl p-6 text-center cursor-pointer transition-colors ${isUploading ? 'opacity-50' : 'hover:border-[var(--color-lila-500)] bg-[var(--bg-surface)]'}`}
                >
                  <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} accept=".pdf,.docx,.txt" />
                  <UploadCloud className="w-8 h-8 text-[var(--color-anthracite-400)] mx-auto mb-2" />
                  <h3 className="text-sm font-medium mb-1 text-[var(--foreground)]">Upload a Document</h3>
                  {isUploading && (
                    <div className="mt-4 max-w-xs mx-auto">
                      <div className="w-full bg-[var(--color-anthracite-800)] rounded-full h-1.5 overflow-hidden">
                        <div className="bg-[var(--color-lila-500)] h-1.5 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Documents List */}
                <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                  <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex justify-between items-center">
                    <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                      Recent Documents
                    </h3>
                  </div>
                  <div className="divide-y divide-[var(--border-surface)] max-h-[300px] overflow-y-auto">
                    {isLoadingDocs ? (
                      <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">Loading...</div>
                    ) : documents.length === 0 ? (
                      <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">No documents uploaded.</div>
                    ) : (
                      documents.slice(0, 5).map((doc: any) => (
                        <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-[var(--bg-surface-hover)] transition-colors">
                          <div className="flex items-center gap-3 truncate">
                            <FileText className="w-4 h-4 text-[var(--color-anthracite-400)] shrink-0" />
                            <span className="text-sm font-medium truncate">{doc.title}</span>
                          </div>
                          <StatusBadge status="neutral" label={doc.status || 'Processing'} />
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Drafts List */}
                <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                  <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex justify-between items-center">
                    <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
                      <PenTool className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                      Recent Drafts
                    </h3>
                    <Button variant="ghost" size="sm" onClick={handleCreateDraft} disabled={isCreatingDraft}>
                      {isCreatingDraft ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                      New
                    </Button>
                  </div>
                  <div className="divide-y divide-[var(--border-surface)] max-h-[200px] overflow-y-auto">
                    {isLoadingDrafts ? (
                      <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">Loading...</div>
                    ) : drafts.length === 0 ? (
                      <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">No drafts found.</div>
                    ) : (
                      drafts.slice(0, 3).map((draft: any) => (
                        <Link href={`/drafts/${draft.id}`} key={draft.id} className="p-4 flex flex-col hover:bg-[var(--bg-surface-hover)] transition-colors block">
                          <span className="text-sm font-medium mb-1">{draft.title}</span>
                          <span className="text-xs text-[var(--color-anthracite-400)]">Last edited: {new Date(draft.updated_at).toLocaleDateString()}</span>
                        </Link>
                      ))
                    )}
                  </div>
                </div>

              </div>

              {/* Right Column: Claims / QA */}
              <div className="lg:col-span-3 space-y-6">
                
                <div className="glass-card rounded-xl border border-[var(--border-surface)] p-4 bg-[var(--bg-surface)]">
                  <h3 className="font-semibold text-[var(--foreground)] mb-4 flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-[var(--color-lila-500)]" />
                    Matter QA
                  </h3>
                  <Button className="w-full justify-start" variant="outline" render={<Link href={`/matters/${matterId}/qa`} />}>
                    Ask AI about Matter
                  </Button>
                  <Button className="w-full justify-start mt-2" variant="outline" onClick={handleRebuildMesa} disabled={isRebuilding}>
                    {isRebuilding && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                    Sync MESA Core
                  </Button>
                </div>

                <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                  <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
                    <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
                      <LayoutTemplate className="w-4 h-4 text-orange-400" />
                      Claims Summary
                    </h3>
                  </div>
                  <div className="p-4 space-y-4 max-h-[500px] overflow-y-auto">
                    {isLoadingClaims ? (
                      <div className="text-center text-sm text-[var(--color-anthracite-400)]">Loading...</div>
                    ) : claims.length === 0 ? (
                      <div className="text-center text-sm text-[var(--color-anthracite-400)]">No claims extracted.</div>
                    ) : (
                      claims.slice(0, 4).map((claim: any) => (
                        <div key={claim.id} className="text-sm border-l-2 border-orange-400 pl-3 py-1">
                          <span className="font-medium text-[var(--foreground)] block mb-1">{claim.status}</span>
                          <span className="text-[var(--color-anthracite-400)] line-clamp-3">{claim.description}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>

            </div>
          )}

          {activeTab === 'timeline' && <Timeline matterId={matterId} />}
          {activeTab === 'claims' && <ClaimsEvidence matterId={matterId} />}
          {activeTab === 'research' && <ResearchShell />}
          {activeTab === 'drafts' && <DraftStudioShell matterId={matterId} />}
        </div>
      </div>
    </div>
  )
}
