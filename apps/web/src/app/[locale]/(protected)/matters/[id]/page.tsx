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
  useRebuildMatterMesa,
  useListMatterParties
} from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
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
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'research' | 'drafts'>('overview')
  const [activeDoc, setActiveDoc] = useState<{id: string, url: string, title: string} | null>(null)

  // Fetch all matters and find current to pass to MatterContextHeader
  const { data: mattersResponse, isLoading: isLoadingMatters } = useListMatters()
  const matters = Array.isArray(mattersResponse?.data) ? mattersResponse.data : ((mattersResponse?.data as any)?.items || [])
  const currentMatter = matters.find((m: any) => m.id === matterId) || {
    name: 'Loading...',
    status: '...',
    confidentiality_level: '...',
    legal_hold: false,
    ai_processing_policy: '...',
    access_scope: 'read'
  }
  
  const canEdit = currentMatter.access_scope !== 'read'

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

  const { data: partiesResponse, isLoading: isLoadingParties } = useListMatterParties(matterId)
  const parties = Array.isArray(partiesResponse?.data) ? partiesResponse.data : []

  const { data: deadlinesResponse, isLoading: isLoadingDeadlines } = useListDeadlines({ matter_id: matterId })
  const deadlines = Array.isArray(deadlinesResponse?.data) ? deadlinesResponse.data : []

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
    return <DocumentViewer documentId={activeDoc.id} matterId={matterId} url={activeDoc.url} title={activeDoc.title} onClose={() => setActiveDoc(null)} />
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
          {['overview', 'documents', 'drafts', 'research'].map((tab) => (
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
            <div className="space-y-8">
              {/* Grid 1: Parties */}
              <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
                  <h3 className="font-semibold text-[var(--foreground)]">Matter Parties</h3>
                </div>
                <div className="p-4 overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-[var(--color-anthracite-400)] uppercase bg-[var(--bg-surface-hover)]">
                      <tr>
                        <th className="px-4 py-2 rounded-tl-lg">Name</th>
                        <th className="px-4 py-2">Role</th>
                        <th className="px-4 py-2 rounded-tr-lg">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {isLoadingParties ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">Loading...</td></tr>
                      ) : parties.length === 0 ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">No parties found.</td></tr>
                      ) : (
                        parties.map((p: any) => (
                          <tr key={p.id} className="border-b border-[var(--border-surface)] hover:bg-[var(--bg-surface-hover)] transition-colors">
                            <td className="px-4 py-3 font-medium text-[var(--foreground)]">{p.name}</td>
                            <td className="px-4 py-3 text-[var(--color-anthracite-400)]">{p.role}</td>
                            <td className="px-4 py-3 text-[var(--color-anthracite-400)]">{p.type}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Grid 2: Claims */}
              <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
                  <h3 className="font-semibold text-[var(--foreground)]">Claims</h3>
                </div>
                <div className="p-4 overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-[var(--color-anthracite-400)] uppercase bg-[var(--bg-surface-hover)]">
                      <tr>
                        <th className="px-4 py-2 rounded-tl-lg">Description</th>
                        <th className="px-4 py-2">Claimant ID</th>
                        <th className="px-4 py-2 rounded-tr-lg">Defendant ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {isLoadingClaims ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">Loading...</td></tr>
                      ) : claims.length === 0 ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">No claims found.</td></tr>
                      ) : (
                        claims.map((c: any) => (
                          <tr key={c.id} className="border-b border-[var(--border-surface)] hover:bg-[var(--bg-surface-hover)] transition-colors">
                            <td className="px-4 py-3 font-medium text-[var(--foreground)] max-w-[400px] truncate">{c.description}</td>
                            <td className="px-4 py-3 text-[var(--color-anthracite-400)] truncate max-w-[150px]">{c.claimant_party_id}</td>
                            <td className="px-4 py-3 text-[var(--color-anthracite-400)] truncate max-w-[150px]">{c.defendant_party_id}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Grid 3: Events & Deadlines */}
              <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
                  <h3 className="font-semibold text-[var(--foreground)]">Events & Deadlines</h3>
                </div>
                <div className="p-4 overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-[var(--color-anthracite-400)] uppercase bg-[var(--bg-surface-hover)]">
                      <tr>
                        <th className="px-4 py-2 rounded-tl-lg">Date</th>
                        <th className="px-4 py-2">Description</th>
                        <th className="px-4 py-2 rounded-tr-lg">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {isLoadingDeadlines ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">Loading...</td></tr>
                      ) : deadlines.length === 0 ? (
                        <tr><td colSpan={3} className="px-4 py-4 text-center">No deadlines found.</td></tr>
                      ) : (
                        deadlines.map((d: any) => (
                          <tr key={d.id} className="border-b border-[var(--border-surface)] hover:bg-[var(--bg-surface-hover)] transition-colors">
                            <td className="px-4 py-3 font-medium text-[var(--foreground)] whitespace-nowrap">{d.calculated_date || d.trigger_date || 'Unknown'}</td>
                            <td className="px-4 py-3 text-[var(--color-anthracite-400)]">{d.description || d.trigger_event}</td>
                            <td className="px-4 py-3"><StatusBadge status="neutral" label={d.status} /></td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-6">
              {/* Upload Action */}
              {canEdit && (
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
              )}

              {/* Documents List */}
              <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
                <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex justify-between items-center">
                  <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                    Matter Documents
                  </h3>
                </div>
                <div className="divide-y divide-[var(--border-surface)] max-h-[600px] overflow-y-auto">
                  {isLoadingDocs ? (
                    <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">Loading...</div>
                  ) : documents.length === 0 ? (
                    <div className="p-4 text-center text-sm text-[var(--color-anthracite-400)]">No documents uploaded.</div>
                  ) : (
                    documents.map((doc: any) => (
                      <div 
                        key={doc.id} 
                        className="p-4 flex items-center justify-between hover:bg-[var(--bg-surface-hover)] transition-colors cursor-pointer"
                        onClick={() => setActiveDoc({ id: doc.id, url: doc.presigned_url || '#', title: doc.title })}
                      >
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
            </div>
          )}

          {activeTab === 'research' && <ResearchShell />}
          {activeTab === 'drafts' && <DraftStudioShell matterId={matterId} />}
        </div>
      </div>
    </div>
  )
}
