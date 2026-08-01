'use client'

import { use, useState } from 'react'
import { useListEvidence } from '@/api/endpoints/default/default'
import { ArrowLeft, Loader2, AlertCircle, FileText, Search, Link as LinkIcon, Database } from 'lucide-react'
import Link from 'next/link'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'

export default function MatterEvidencePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  const { data: evidenceResponse, isLoading: loading, isError, refetch } = useListEvidence(matterId)
  const evidences = Array.isArray(evidenceResponse) ? evidenceResponse : []
  
  const [search, setSearch] = useState('')

  const filteredEvidence = evidences.filter((ev) =>
    ev.description.toLowerCase().includes(search.toLowerCase()) ||
    ev.id?.toLowerCase().includes(search.toLowerCase()) ||
    ev.document_id?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Matter Overview
      </Link>
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Evidence Matrix</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Review evidence artifacts and their linked claims.</p>
        </div>
      </div>

      <div className="relative w-full md:max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
        <Input 
          type="text" 
          placeholder="Search evidence text, ID or Document ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 w-full"
        />
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <Loader2 className="animate-spin h-8 w-8 text-[var(--color-lila-500)]" />
            <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading evidence...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <AlertCircle className="w-12 h-12 text-[var(--color-semantic-error)]" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">Failed to load evidence</h3>
            <Button variant="outline" onClick={() => refetch()}>Retry</Button>
          </div>
        ) : filteredEvidence.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Database className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Evidence Found</h3>
            <p className="text-[var(--color-anthracite-500)]">No evidence artifacts have been extracted yet.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead className="w-[40%]">Extracted Content</TableHead>
                <TableHead>Source Document</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Linked Claims</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEvidence.map((ev) => (
                <TableRow key={ev.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell>
                    <div className="font-medium text-sm text-[var(--foreground)] line-clamp-3">
                      {ev.description}
                    </div>
                  </TableCell>
                  <TableCell>
                    {ev.document_id ? (
                      <Link href={`/documents/${ev.document_id}`} className="inline-flex items-center gap-1.5 text-sm text-[var(--color-lila-500)] hover:underline">
                        <FileText className="w-4 h-4" />
                        {ev.document_id.substring(0, 8)}
                      </Link>
                    ) : (
                      <span className="text-sm text-[var(--color-anthracite-400)] italic">System Generated</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge 
                      status={ev.review_status === 'APPROVED' ? 'success' : ev.review_status === 'REJECTED' ? 'error' : 'review-required'}
                      label={ev.review_status}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <LinkIcon className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                      <span className="text-sm text-[var(--color-anthracite-500)]">Not exposed</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-xs text-[var(--color-anthracite-500)]">Locator {ev.source_locator_id?.slice(0, 8) ?? 'pending'}</span>
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
