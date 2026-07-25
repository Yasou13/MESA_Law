'use client'
import { useState, use } from 'react'
import Link from 'next/link'
import { useListDocuments, useCreateUploadIntent } from '@/api/endpoints/default/default'
import axios from 'axios'

import { Timeline } from '@/components/matters/Timeline'
import { ClaimsEvidence } from '@/components/matters/ClaimsEvidence'
import { QAShell } from '@/components/matters/QAShell'
import { ResearchShell } from '@/components/matters/ResearchShell'

export default function MatterDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'claims' | 'research'>('overview');

  const { data: documentsResponse, refetch: refetchDocs } = useListDocuments(matterId);
  const documents = documentsResponse?.data || [];
  const { mutateAsync: createIntent } = useCreateUploadIntent();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setUploadStatus('uploading');
      
      const res = await createIntent({
        data: {
          matter_id: matterId,
          filename: file.name,
          mime_type: file.type || 'application/octet-stream'
        }
      });
      
      const presigned_url = (res as any).presigned_url || (res.data as any).presigned_url;
      
      await axios.put(presigned_url, file, {
        headers: {
          'Content-Type': file.type || 'application/octet-stream'
        }
      });

      setUploadStatus('success');
      setFile(null);
      refetchDocs();
    } catch (error) {
      console.error('Upload failed', error);
      setUploadStatus('error');
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto h-screen flex flex-col">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/matters" className="text-zinc-400 hover:text-white transition-colors text-sm mb-2 block">← Back to Matters</Link>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Matter {matterId}</h1>
        </div>
        <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1">
          {['overview', 'timeline', 'claims', 'research'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === tab ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4 text-zinc-100">Upload Document</h2>
                <div className="flex gap-4 items-center">
                  <input 
                    type="file" 
                    onChange={handleFileChange}
                    className="block w-full text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-zinc-800 file:text-blue-400 hover:file:bg-zinc-700 transition-colors"
                  />
                  <button 
                    onClick={handleUpload}
                    disabled={!file || uploadStatus === 'uploading'}
                    className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white px-6 py-2 rounded-full font-medium transition-colors"
                  >
                    {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload'}
                  </button>
                </div>
                {uploadStatus === 'success' && <p className="text-green-400 mt-4 text-sm font-medium">Upload complete!</p>}
                {uploadStatus === 'error' && <p className="text-red-400 mt-4 text-sm font-medium">Upload failed.</p>}
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4 text-zinc-100">Documents</h2>
                {documents && documents.length > 0 ? (
                  <ul className="space-y-3">
                    {documents.map((doc: any) => (
                      <li key={doc.id} className="text-zinc-300 bg-zinc-950 px-4 py-3 rounded-lg border border-zinc-800 flex items-center justify-between">
                        <span className="font-medium">{doc.title}</span>
                        <span className="text-xs text-zinc-500 font-mono">{doc.id.substring(0, 8)}...</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-zinc-500 text-sm">No documents uploaded yet.</p>
                )}
              </div>
            </div>
            
            <div className="lg:col-span-1">
              <QAShell />
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-sm min-h-[500px]">
            <Timeline />
          </div>
        )}

        {activeTab === 'claims' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-sm min-h-[500px]">
            <ClaimsEvidence />
          </div>
        )}

        {activeTab === 'research' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl shadow-sm min-h-[500px]">
            <ResearchShell />
          </div>
        )}
      </div>
    </div>
  )
}
