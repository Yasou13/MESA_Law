'use client'

import { useParams } from 'next/navigation'
import { useGetDocument, useDownloadDocument } from '@/api/endpoints/default/default'
import { AlertTriangle, ArrowLeft, Clock, FileText, Download } from 'lucide-react'
import Link from 'next/link'

export default function DocumentViewerPage() {
  const params = useParams()
  const documentId = params.id as string

  const { data: docRes, isLoading: loadingDoc } = useGetDocument(documentId)
  const { data: dlRes, isLoading: loadingDl, isError: dlError } = useDownloadDocument(documentId, {
    query: {
      enabled: ['CLEAN', 'PARSED', 'READY'].includes(docRes?.status.toUpperCase() ?? '')
    }
  })

  const doc = docRes
  const presignedUrl = dlRes?.presigned_url



  if (loadingDoc) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
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

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col md:flex-row bg-[var(--background)] overflow-hidden">
      {/* Left Panel: Document Viewer */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-[var(--border-surface)]">
        <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-wrap items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <Link href="/documents" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg transition-colors shrink-0">
              <ArrowLeft className="w-5 h-5 text-[var(--color-anthracite-400)]" />
            </Link>
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-[var(--color-lila-500)] shrink-0" />
                <h1 className="text-lg font-bold tracking-tight truncate text-[var(--foreground)]">{doc.title}</h1>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3 shrink-0">
            <span className={`text-xs font-medium px-2 py-1 rounded-md border ${
              ['CLEAN', 'PARSED', 'READY'].includes(doc.status.toUpperCase()) ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
              ['PROCESSING', 'SCANNING', 'PARSING'].includes(doc.status.toUpperCase()) ? 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20' :
              'bg-red-500/10 text-red-400 border-red-500/20'
            }`}>
              {doc.status?.toUpperCase()}
            </span>
            {presignedUrl && (
              <a 
                href={presignedUrl} 
                download
                className="flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-surface-hover)] hover:bg-[var(--bg-surface)] text-[var(--foreground)] border border-[var(--border-surface)] rounded-lg transition-colors text-xs font-medium"
              >
                <Download className="w-4 h-4" />
                Original
              </a>
            )}
          </div>
        </div>

        <div className="flex-1 bg-zinc-950 relative overflow-hidden">
          {['CLEAN', 'PARSED', 'READY'].includes(doc.status.toUpperCase()) && presignedUrl ? (
            <iframe 
              src={`${presignedUrl}#toolbar=0`} 
              className="w-full h-full border-none bg-white rounded-none"
              title={doc.title}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-surface)] p-6">
              <div className={`text-center max-w-md p-8 rounded-2xl border shadow-sm ${['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase()) ? 'bg-red-500/5 border-red-500/20' : 'bg-[var(--bg-surface-hover)] border-[var(--border-surface)]'}`}>
                {['CLEAN', 'PARSED', 'READY'].includes(doc.status.toUpperCase()) && loadingDl && (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)] mx-auto mb-4"></div>
                )}
                {['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase()) && (
                  <div className="bg-red-500/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                  </div>
                )}
                {['UPLOADING', 'VERIFYING', 'SCANNING', 'PARSING', 'PROCESSING'].includes(doc.status.toUpperCase()) && (
                  <Clock className="w-12 h-12 text-[var(--color-anthracite-400)] mx-auto mb-4 animate-pulse" />
                )}
                <h3 className={`text-xl font-bold mb-2 ${['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase()) ? 'text-red-500' : 'text-[var(--foreground)]'}`}>
                  {['CLEAN', 'PARSED', 'READY'].includes(doc.status.toUpperCase()) && dlError ? 'Failed to load preview' :
                   ['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase()) ? 'SECURITY ALERT' : 'Preview Unavailable'}
                </h3>
                <p className={`text-sm ${['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase()) ? 'text-red-400' : 'text-[var(--color-anthracite-400)]'}`}>
                  {['CLEAN', 'PARSED', 'READY'].includes(doc.status.toUpperCase())
                    ? 'We could not generate a secure preview URL for this document.' 
                    : ['QUARANTINED', 'INFECTED', 'BLOCKED'].includes(doc.status.toUpperCase())
                      ? doc.failure_reason ?? 'This document failed a security or validation check and cannot be accessed.'
                      : `Current state: ${doc.status}. Preview is available only after successful processing.`}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
