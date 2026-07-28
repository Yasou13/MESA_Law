'use client'

import { useListAllDocuments, downloadDocument } from '@/api/endpoints/default/default'
import { FileText, Folder, CheckCircle, AlertTriangle, Clock, Search, Download, Eye, MessageSquare } from 'lucide-react'
import Link from 'next/link'
import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'
import { DocumentViewer } from '@/features/documents/components/DocumentViewer'
import { toast } from 'react-hot-toast'

export default function GlobalDocumentsPage() {
  const { data: res, isLoading, isError, refetch } = useListAllDocuments()
  const [search, setSearch] = useState('')
  const [activeDoc, setActiveDoc] = useState<{url: string, title: string, documentId: string, matterId: string} | null>(null)
  
  const documents = (res?.data as any[]) || []
  const filteredDocuments = documents.filter((doc) => 
    doc.title?.toLowerCase().includes(search.toLowerCase()) || 
    doc.id?.toLowerCase().includes(search.toLowerCase())
  )

  if (activeDoc) {
    return <DocumentViewer documentId={activeDoc.documentId} matterId={activeDoc.matterId} url={activeDoc.url} title={activeDoc.title} onClose={() => setActiveDoc(null)} />
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Global Document Center</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage and view all documents across the platform.</p>
        </div>
      </div>

      <div className="relative w-full md:max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
        <Input 
          type="text" 
          placeholder="Search documents by name or ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 w-full"
        />
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
            <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading documents...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <AlertTriangle className="w-12 h-12 text-[var(--color-semantic-error)]" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">Failed to load documents</h3>
            <Button variant="outline" onClick={() => refetch()}>Retry</Button>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Folder className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Documents Found</h3>
            <p className="text-[var(--color-anthracite-500)]">We couldn't find any documents matching your search.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>Document Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date Added</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocuments.map((doc: any) => (
                <TableRow key={doc.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-[var(--color-anthracite-400)]" />
                      <div>
                        <Link href={`/documents/${doc.id}`} className="hover:text-[var(--color-lila-500)] hover:underline block">{doc.title}</Link>
                        <span className="text-xs text-[var(--color-anthracite-500)] font-mono">{doc.id.substring(0, 8)}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={doc.status === 'clean' ? 'success' : doc.status === 'processing' ? 'neutral' : 'error'} label={doc.status || 'Processing'} />
                  </TableCell>
                  <TableCell className="text-[var(--color-anthracite-500)]">
                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="icon-sm" onClick={async () => {
                        try {
                          const res = await downloadDocument(doc.id)
                          setActiveDoc({ url: (res.data as any).presigned_url, title: doc.title, documentId: doc.id, matterId: doc.matter_id || 'unknown' })
                        } catch (e: any) {
                          toast.error('Cannot view document yet')
                        }
                      }} title="View Document">
                        <Eye className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" onClick={async () => {
                        try {
                          const res = await downloadDocument(doc.id)
                          window.open((res.data as any).presigned_url, '_blank')
                        } catch (e: any) {
                          toast.error('Cannot download document yet')
                        }
                      }} title="Download">
                        <Download className="w-4 h-4 text-[var(--color-semantic-info)]" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" render={<Link href={`/documents/${doc.id}`} />} title="Chat with Document">
                        <MessageSquare className="w-4 h-4 text-[var(--color-lila-500)]" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
