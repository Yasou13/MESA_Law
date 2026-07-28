'use client'

import { useState } from 'react'
import { FileEdit, Search, Plus, Filter, MoreHorizontal, PenTool } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'


// UI Stub for Phase 22
const mockDrafts = [
  { id: '1', title: 'Motion for Summary Judgment', matter: 'Smith v. Jones (IP Dispute)', type: 'Motion', lastModified: '2026-07-28T09:30:00Z', status: 'in-progress' },
  { id: '2', title: 'Response to Interrogatories', matter: 'TechCorp Merger', type: 'Discovery', lastModified: '2026-07-27T14:15:00Z', status: 'review-required' },
  { id: '3', title: 'Initial Disclosures', matter: 'Smith v. Jones (IP Dispute)', type: 'Filing', lastModified: '2026-07-26T11:00:00Z', status: 'approved' },
]

export default function DraftsPage() {
  const [search, setSearch] = useState('')
  const [drafts] = useState(mockDrafts)
  
  const filteredDrafts = drafts.filter(d => 
    d.title.toLowerCase().includes(search.toLowerCase()) || 
    d.matter.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Drafts Studio</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage AI-assisted document drafts and templates.</p>
        </div>
        <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
          <Plus className="w-4 h-4" /> New Draft
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search drafts or matters..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 w-full"
          />
        </div>
        <Button variant="outline" className="gap-2 shrink-0">
          <Filter className="w-4 h-4" /> Filter
        </Button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {filteredDrafts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <FileEdit className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Drafts Found</h3>
            <p className="text-[var(--color-anthracite-500)]">Create a new draft to get started.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>Draft Name</TableHead>
                <TableHead>Matter</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDrafts.map(draft => (
                <TableRow key={draft.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell>
                    <Link href={`/drafts/${draft.id}`} className="flex items-center gap-2 group">
                      <div className="w-8 h-8 rounded-lg bg-[var(--color-lila-500)]/10 flex items-center justify-center shrink-0">
                        <PenTool className="w-4 h-4 text-[var(--color-lila-500)]" />
                      </div>
                      <span className="font-medium text-[var(--foreground)] group-hover:text-[var(--color-lila-400)] transition-colors">{draft.title}</span>
                    </Link>
                  </TableCell>
                  <TableCell className="text-[var(--color-anthracite-400)]">
                    {draft.matter}
                  </TableCell>
                  <TableCell>
                    <span className="px-2 py-1 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded text-xs font-medium text-[var(--color-anthracite-300)]">
                      {draft.type}
                    </span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge 
                      status={draft.status === 'approved' ? 'success' : draft.status === 'in-progress' ? 'processing' : 'review-required'} 
                      label={draft.status.replace('-', ' ').toUpperCase()} 
                    />
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-500)]">
                    {new Date(draft.lastModified).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link href={`/drafts/${draft.id}`}>
                        <Button variant="ghost" size="icon-sm" title="Edit Draft">
                          <FileEdit className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                        </Button>
                      </Link>
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
