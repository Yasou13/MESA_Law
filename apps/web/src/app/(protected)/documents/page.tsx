'use client'

import { useListAllDocuments } from '@/api/endpoints/default/default'
import { FileText, Folder, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import Link from 'next/link'

export default function DocumentsPage() {
  const { data: res, isLoading, isError, refetch } = useListAllDocuments()
  
  const documents = (res?.data as any[]) || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Failed to load documents</h2>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-[var(--color-anthracite-700)] text-white rounded-lg hover:bg-[var(--color-anthracite-600)]"
        >
          Retry
        </button>
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'clean': return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'infected':
      case 'quarantined': return <AlertTriangle className="w-4 h-4 text-red-400" />
      default: return <Clock className="w-4 h-4 text-orange-400" />
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Document Center</h1>
          <p className="text-zinc-400">View and manage all your documents across matters.</p>
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden divide-y divide-[var(--border-surface)]">
        {documents.length === 0 ? (
          <div className="p-12 text-center text-zinc-400">
            <Folder className="w-12 h-12 text-zinc-500/50 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No Documents</h3>
            <p>You haven&apos;t uploaded any documents yet.</p>
          </div>
        ) : (
          documents.map((doc: any) => (
            <Link key={doc.id} href={`/documents/${doc.id}`} className="block hover:bg-[var(--bg-surface-hover)] transition-colors">
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] flex items-center justify-center">
                    <FileText className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">{doc.title}</h3>
                    <p className="text-xs text-zinc-500 font-mono mt-1">ID: {doc.id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-full">
                  {getStatusIcon(doc.status)}
                  <span className="text-xs font-medium uppercase tracking-wider">{doc.status}</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
