'use client'

import { useParams } from 'next/navigation'
import { useGetDocument, useDownloadDocument } from '@/api/endpoints/default/default'
import { FileText, Download, AlertTriangle, ArrowLeft, Clock } from 'lucide-react'
import Link from 'next/link'

export default function DocumentViewerPage() {
  const params = useParams()
  const documentId = params.id as string

  const { data: docRes, isLoading: loadingDoc } = useGetDocument(documentId)
  const { data: dlRes, isLoading: loadingDl, isError: dlError } = useDownloadDocument(documentId, {
    query: {
      enabled: (docRes?.data as any)?.status === 'clean'
    }
  })

  const doc = docRes?.data as any

  if (loadingDoc) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Document not found</h2>
      </div>
    )
  }

  const presignedUrl = (dlRes?.data as any)?.presigned_url

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/documents" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-purple-400" />
              <h1 className="text-2xl font-bold tracking-tight truncate max-w-xl">{doc.title}</h1>
            </div>
            <p className="text-zinc-500 text-sm mt-1">Status: <span className="font-medium uppercase tracking-wider text-[var(--foreground)]">{doc?.status}</span></p>
          </div>
        </div>
        
        {presignedUrl && (
          <a 
            href={presignedUrl} 
            download
            className="flex items-center gap-2 px-4 py-2 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors text-sm font-medium"
          >
            <Download className="w-4 h-4" />
            Download Original
          </a>
        )}
      </div>

      <div className="flex-1 glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden min-h-[600px] relative">
        {doc?.status === 'clean' && presignedUrl ? (
          <iframe 
            src={presignedUrl} 
            className="w-full h-full border-none bg-white"
            title={doc.title}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-surface-hover)] p-4">
            <div className={`text-center max-w-lg p-8 rounded-2xl border ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'bg-red-500/10 border-red-500/30' : 'bg-[var(--bg-surface)] border-[var(--border-surface)]'}`}>
              {doc?.status === 'clean' && loadingDl && (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)] mx-auto mb-4"></div>
              )}
              {(doc?.status === 'quarantined' || doc?.status === 'infected') && (
                <div className="bg-red-500/20 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(239,68,68,0.3)]">
                  <AlertTriangle className="w-10 h-10 text-red-500" />
                </div>
              )}
              {doc?.status === 'scanning' && (
                <Clock className="w-12 h-12 text-orange-400 mx-auto mb-4" />
              )}
              <h3 className={`text-2xl font-bold mb-3 ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'text-red-500' : ''}`}>
                {doc?.status === 'clean' && dlError ? 'Failed to load preview' : 
                 (doc?.status === 'quarantined' || doc?.status === 'infected') ? 'SECURITY ALERT: Document Quarantined' : 'Preview Unavailable'}
              </h3>
              <p className={`text-base ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'text-red-400/90' : 'text-zinc-400'}`}>
                {doc?.status === 'clean' 
                  ? 'We could not generate a secure preview URL for this document.' 
                  : (doc?.status === 'quarantined' || doc?.status === 'infected') 
                    ? 'This document has failed security checks (virus/malware detected or invalid format). Access is strictly prohibited.'
                    : 'This document is currently being scanned. Preview will be available once the security scan completes.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
