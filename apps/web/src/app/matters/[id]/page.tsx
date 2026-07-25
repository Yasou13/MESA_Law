'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState, useRef, use } from 'react'
import { FileText, UploadCloud, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { toast } from 'react-hot-toast'
import Link from 'next/link'
import { Timeline } from '@/components/matters/Timeline'
import { ClaimsEvidence } from '@/components/matters/ClaimsEvidence'
import { ResearchShell } from '@/components/matters/ResearchShell'
import { QAShell } from '@/components/matters/QAShell'
import { DraftStudioShell } from '@/components/matters/DraftStudioShell'

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

  const { data: documents, isLoading: isLoadingDocs } = useQuery<Document[]>({
    queryKey: ['documents', matterId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/documents/matter/${matterId}`)
      return res.data
    },
    refetchInterval: (query) => {
      const docs = query.state.data
      if (docs?.some(d => d.status === 'uploading' || d.status === 'scanning' || d.status === 'processing')) {
        return 3000
      }
      return false
    }
  })

  const { data: claims, isLoading: isLoadingClaims } = useQuery({
    queryKey: ['claims', matterId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/matters/${matterId}/claims`)
      return res.data
    }
  })

  const { data: parties, isLoading: isLoadingParties } = useQuery({
    queryKey: ['parties', matterId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/matters/${matterId}/parties`)
      return res.data
    }
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setIsUploading(true)
      setUploadProgress(0)

      // 1. Get Presigned URL
      const intentRes = await axios.post('/api/v1/documents/upload-intent', {
        matter_id: matterId,
        filename: file.name,
        mime_type: file.type || 'application/octet-stream'
      })
      
      const { document_id, presigned_url } = intentRes.data

      // 2. Upload directly to S3
      await axios.put(presigned_url, file, {
        headers: {
          'Content-Type': file.type || 'application/octet-stream'
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(percentCompleted)
          }
        }
      })

      // 3. Notify backend upload is complete
      await axios.post(`/api/v1/documents/${document_id}/complete`)
      
      toast.success('File uploaded successfully! Scanning in progress.')
      queryClient.invalidateQueries({ queryKey: ['documents', matterId] })
      
    } catch (error) {
      console.error(error)
      toast.error('Upload failed')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <Link href="/matters" className="text-zinc-400 hover:text-white transition-colors text-sm mb-4 inline-block">
          &larr; Back to Matters
        </Link>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Matter {matterId}</h1>
          <div className="flex gap-2 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'timeline' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Timeline
            </button>
            <button
              onClick={() => setActiveTab('claims')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'claims' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Claims
            </button>
            <button
              onClick={() => setActiveTab('research')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'research' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Research
            </button>
            <button
              onClick={() => setActiveTab('drafts')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'drafts' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Draft Studio
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'overview' && (
        <>
          <div className="mb-12 bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <QAShell matterId={matterId} />
          </div>

          <h2 className="text-xl font-semibold mb-6">Matter Documents</h2>

          {/* Upload Area */}
      <div className="mb-10">
        <div 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed border-zinc-700 rounded-xl p-12 text-center cursor-pointer transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-500 hover:bg-blue-500/5'}`}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt"
          />
          <UploadCloud className="w-12 h-12 text-zinc-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Upload a Document</h3>
          <p className="text-sm text-zinc-500">Drag & drop or click to browse</p>
          
          {isUploading && (
            <div className="mt-6 max-w-md mx-auto">
              <div className="flex justify-between text-xs text-zinc-400 mb-2">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-blue-500 h-2 transition-all duration-300" 
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Documents List */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold mb-6">Files</h2>
        {isLoadingDocs ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
          </div>
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-800/50 text-zinc-400">
                <tr>
                  <th className="px-6 py-4 font-medium">Document Name</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {documents?.map((doc) => (
                  <tr key={doc.id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-zinc-400" />
                        <span className="font-medium text-zinc-200">{doc.title}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-800 text-zinc-300">
                        {doc.status || 'Processing'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={async () => {
                          try {
                            const res = await axios.get(`/api/v1/documents/${doc.id}/download`)
                            window.open(res.data.presigned_url, '_blank')
                          } catch (error: any) {
                            toast.error(error.response?.data?.detail || 'Cannot download document yet')
                          }
                        }}
                        className="text-blue-400 hover:text-blue-300 font-medium"
                      >
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
                {documents?.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-6 py-12 text-center text-zinc-500">
                      No documents uploaded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Extracted Data */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div>
          <h2 className="text-xl font-semibold mb-6">Parties</h2>
          {isLoadingParties ? (
             <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
          ) : (
            <div className="space-y-4">
              {parties?.map((party: any) => (
                <div key={party.id} className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
                  <div className="font-medium">{party.name}</div>
                  <div className="text-sm text-zinc-500">{party.role} • {party.type}</div>
                </div>
              ))}
              {parties?.length === 0 && <p className="text-sm text-zinc-500">No parties extracted yet.</p>}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-6">Claims</h2>
          {isLoadingClaims ? (
             <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
          ) : (
            <div className="space-y-4">
              {claims?.map((claim: any) => (
                <div key={claim.id} className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl">
                  <div className="font-medium text-sm mb-2 text-blue-400">{claim.status.toUpperCase()}</div>
                  <p className="text-zinc-300">{claim.description}</p>
                </div>
              ))}
              {claims?.length === 0 && <p className="text-sm text-zinc-500">No claims extracted yet.</p>}
            </div>
          )}
        </div>
      </div>
      </>
      )}

      {activeTab === 'timeline' && <Timeline matterId={matterId} />}
      {activeTab === 'claims' && <ClaimsEvidence matterId={matterId} />}
      {activeTab === 'research' && <ResearchShell />}
      {activeTab === 'drafts' && <DraftStudioShell matterId={matterId} />}
    </div>
  )
}
