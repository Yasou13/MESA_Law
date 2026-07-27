'use client'

import { useQueryClient } from '@tanstack/react-query'
import { useState, useRef, use } from 'react'
import { FileText, UploadCloud, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Link from 'next/link'
import { DocumentViewer } from '@/components/DocumentViewer'
import { Timeline } from '@/components/matters/Timeline'
import { ClaimsEvidence } from '@/components/matters/ClaimsEvidence'
import { ResearchShell } from '@/components/matters/ResearchShell'
import { QAShell } from '@/components/matters/QAShell'
import { DraftStudioShell } from '@/components/matters/DraftStudioShell'
import {
  useListMatterDocuments,
  useListClaims,
  useListMatterParties,
  useCreateUploadIntent,
  useCompleteUpload,
  downloadDocument
} from '@/api/endpoints/default/default'

type Document = {
  id: string
  title: string
  status?: string
}

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'claims' | 'research' | 'drafts'>('overview')
  const [activeDoc, setActiveDoc] = useState<{url: string, title: string} | null>(null)

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

  const uploadIntent = useCreateUploadIntent()
  const completeUpload = useCompleteUpload()

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // 1. Get Presigned URL via intent
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
      
      // 2. Upload direct to MinIO (or backend bypass)
      setUploadProgress(50)
      await fetch(presigned_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/pdf'
        }
      })
      setUploadProgress(90)

      // 3. Mark complete
      await completeUpload.mutateAsync({ documentId: document_id })
      
      setUploadProgress(100)
      toast.success('Document uploaded successfully')
      queryClient.invalidateQueries({ queryKey: [`/api/v1/documents/matter/${matterId}`] })
    } catch (err) {
      console.error(err)
      toast.error('Upload failed')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  if (activeDoc) {
    return <DocumentViewer url={activeDoc.url} title={activeDoc.title} onClose={() => setActiveDoc(null)} />
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <Link href="/matters" className="text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors text-sm mb-4 inline-block">
          &larr; Back to Matters
        </Link>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Matter {matterId}</h1>
          <div className="flex gap-2 bg-[var(--bg-surface-hover)] p-1 rounded-lg border border-[var(--border-surface)]">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-[var(--color-lila-500)] text-white shadow-sm' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]'}`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'timeline' ? 'bg-[var(--color-lila-500)] text-white shadow-sm' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]'}`}
            >
              Timeline
            </button>
            <button
              onClick={() => setActiveTab('claims')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'claims' ? 'bg-[var(--color-lila-500)] text-white shadow-sm' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]'}`}
            >
              Claims
            </button>
            <button
              onClick={() => setActiveTab('research')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'research' ? 'bg-[var(--color-lila-500)] text-white shadow-sm' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]'}`}
            >
              Research
            </button>
            <button
              onClick={() => setActiveTab('drafts')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'drafts' ? 'bg-[var(--color-lila-500)] text-white shadow-sm' : 'text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]'}`}
            >
              Draft Studio
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-12">
          <div className="mb-12 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl p-6 shadow-sm">
            <QAShell matterId={matterId} />
          </div>

          <h2 className="text-xl font-semibold mb-6 text-[var(--foreground)]">Matter Documents</h2>

          {/* Upload Area */}
          <div className="mb-10">
            <div 
              onClick={() => !isUploading && fileInputRef.current?.click()}
              className={`border-2 border-dashed border-[var(--color-anthracite-700)] rounded-xl p-12 text-center cursor-pointer transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-[var(--color-lila-500)] hover:bg-[var(--color-lila-500)]/5 bg-[var(--bg-surface)]'}`}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                onChange={handleFileUpload}
                accept=".pdf,.docx,.txt"
              />
              <UploadCloud className="w-12 h-12 text-[var(--color-anthracite-400)] mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2 text-[var(--foreground)]">Upload a Document</h3>
              <p className="text-sm text-[var(--color-anthracite-400)]">Drag & drop or click to browse</p>
              
              {isUploading && (
                <div className="mt-6 max-w-md mx-auto">
                  <div className="flex justify-between text-xs text-[var(--color-anthracite-300)] mb-2">
                    <span>Uploading...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-[var(--color-anthracite-800)] rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-[var(--color-lila-500)] h-2 transition-all duration-300 shadow-[0_0_10px_var(--color-lila-500)]" 
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Documents List */}
          <div className="mb-12">
            <h2 className="text-xl font-semibold mb-6 text-[var(--foreground)]">Files</h2>
            {isLoadingDocs ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-6 h-6 animate-spin text-[var(--color-lila-500)]" />
              </div>
            ) : (
              <div className="bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[var(--bg-surface-hover)] text-[var(--color-anthracite-400)] border-b border-[var(--border-surface)]">
                    <tr>
                      <th className="px-6 py-4 font-medium">Document Name</th>
                      <th className="px-6 py-4 font-medium">Status</th>
                      <th className="px-6 py-4 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-surface)]">
                    {documents?.map((doc) => (
                      <tr key={doc.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-[var(--color-anthracite-400)]" />
                            <span className="font-medium text-[var(--foreground)] group-hover:text-[var(--color-lila-500)] transition-colors">{doc.title}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[var(--color-anthracite-800)] text-[var(--color-anthracite-200)] border border-[var(--color-anthracite-700)]">
                            {doc.status || 'Processing'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right flex justify-end gap-3">
                          <button 
                            onClick={async () => {
                              try {
                                const res = await downloadDocument(doc.id)
                                setActiveDoc({ url: (res.data as any).presigned_url, title: doc.title })
                              } catch (error: any) {
                                toast.error(error.response?.data?.detail || 'Cannot view document yet')
                              }
                            }}
                            className="text-[var(--foreground)] hover:text-[var(--color-lila-500)] font-medium transition-colors"
                          >
                            View
                          </button>
                          <button 
                            onClick={async () => {
                              try {
                                const res = await downloadDocument(doc.id)
                                window.open((res.data as any).presigned_url, '_blank')
                              } catch (error: any) {
                                toast.error(error.response?.data?.detail || 'Cannot download document yet')
                              }
                            }}
                            className="text-[var(--color-semantic-info)] hover:text-[var(--color-semantic-info-hover)] font-medium transition-colors"
                          >
                            Download
                          </button>
                        </td>
                      </tr>
                    ))}
                    {documents?.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-6 py-12 text-center text-[var(--color-anthracite-400)]">
                          No documents uploaded yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Extracted Data */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div>
          <h2 className="text-xl font-semibold mb-6 text-[var(--foreground)]">Parties</h2>
          {isLoadingParties ? (
             <Loader2 className="w-6 h-6 animate-spin text-[var(--color-lila-500)]" />
          ) : (
            <div className="space-y-4">
              {parties?.map((party: any) => (
                <div key={party.id} className="p-4 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl shadow-sm">
                  <div className="font-medium text-[var(--foreground)]">{party.name}</div>
                  <div className="text-sm text-[var(--color-anthracite-400)]">{party.role} • {party.type}</div>
                </div>
              ))}
              {parties?.length === 0 && <p className="text-sm text-[var(--color-anthracite-400)]">No parties extracted yet.</p>}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-6 text-[var(--foreground)]">Claims</h2>
          {isLoadingClaims ? (
             <Loader2 className="w-6 h-6 animate-spin text-[var(--color-lila-500)]" />
          ) : (
            <div className="space-y-4">
              {claims?.map((claim: any) => (
                <div key={claim.id} className="p-4 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl shadow-sm">
                  <div className="font-medium text-sm mb-2 text-[var(--color-semantic-info)]">{claim.status.toUpperCase()}</div>
                  <p className="text-[var(--color-anthracite-200)]">{claim.description}</p>
                </div>
              ))}
              {claims?.length === 0 && <p className="text-sm text-[var(--color-anthracite-400)]">No claims extracted yet.</p>}
            </div>
          )}
        </div>
      </div>

      {activeTab === 'timeline' && <Timeline matterId={matterId} />}
      {activeTab === 'claims' && <ClaimsEvidence matterId={matterId} />}
      {activeTab === 'research' && <ResearchShell />}
      {activeTab === 'drafts' && <DraftStudioShell matterId={matterId} />}
    </div>
  )
}
