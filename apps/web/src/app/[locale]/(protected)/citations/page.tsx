'use client'

import { useState } from 'react'
import { BookOpen, Search, Filter, MoreHorizontal, CheckCircle2, AlertTriangle, XCircle, Link as LinkIcon, Download } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'


// UI Stub for Phase 24
const mockCitations = [
  { 
    id: '1', 
    citation: 'Smith v. Jones, 123 F.3d 456 (9th Cir. 2024)', 
    matter: 'Smith v. Jones (IP Dispute)', 
    document: 'Motion for Summary Judgment', 
    format: 'Bluebook 21st', 
    status: 'valid',
    description: 'Good law. No negative history found.'
  },
  { 
    id: '2', 
    citation: 'TechCorp v. Startup LLC, 456 U.S. 789 (2020)', 
    matter: 'TechCorp Merger', 
    document: 'Response to Interrogatories', 
    format: 'Bluebook 21st', 
    status: 'warning',
    description: 'Distinguished by recent circuit court ruling.'
  },
  { 
    id: '3', 
    citation: 'OldLaw Inc. v. Obsolete Corp., 12 F.2d 34 (1930)', 
    matter: 'Smith v. Jones (IP Dispute)', 
    document: 'Initial Disclosures', 
    format: 'Bluebook 21st', 
    status: 'invalid',
    description: 'Overruled by statute in 1985.'
  },
]

export default function CitationsPage() {
  const [search, setSearch] = useState('')
  const [citations] = useState(mockCitations)
  
  const filteredCitations = citations.filter(c => 
    c.citation.toLowerCase().includes(search.toLowerCase()) || 
    c.matter.toLowerCase().includes(search.toLowerCase()) ||
    c.document.toLowerCase().includes(search.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'valid': return <CheckCircle2 className="w-5 h-5 text-emerald-500" />
      case 'warning': return <AlertTriangle className="w-5 h-5 text-amber-500" />
      case 'invalid': return <XCircle className="w-5 h-5 text-red-500" />
      default: return null
    }
  }

  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'valid': return <StatusBadge status="success" label="GOOD LAW" />
      case 'warning': return <StatusBadge status="warning" label="CAUTION" />
      case 'invalid': return <StatusBadge status="error" label="OVERRULED" />
      default: return null
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Citation Manager</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Verify citations, check Bluebook formatting, and monitor negative treatment.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" /> Export Table of Authorities
          </Button>
          <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
            <CheckCircle2 className="w-4 h-4" /> Run Global Cite Check
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search citations, matters, or documents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 w-full"
          />
        </div>
        <Button variant="outline" className="gap-2 shrink-0">
          <Filter className="w-4 h-4" /> Filter Status
        </Button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {filteredCitations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <BookOpen className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Citations Found</h3>
            <p className="text-[var(--color-anthracite-500)]">Draft documents to automatically extract and verify citations.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead className="w-[30%]">Citation</TableHead>
                <TableHead>Treatment</TableHead>
                <TableHead>Source Document</TableHead>
                <TableHead>Format</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCitations.map(cit => (
                <TableRow key={cit.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell>
                    <div className="font-medium text-[var(--foreground)] flex items-start gap-2">
                      <div className="mt-0.5">{getStatusIcon(cit.status)}</div>
                      <div>
                        <span className="font-serif leading-relaxed text-[15px]">{cit.citation}</span>
                        <div className="text-xs text-[var(--color-anthracite-500)] mt-1">{cit.matter}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1.5 items-start">
                      {getStatusLabel(cit.status)}
                      <span className="text-xs text-[var(--color-anthracite-400)] truncate max-w-[200px]" title={cit.description}>
                        {cit.description}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Link href="#" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-lila-500)] hover:underline">
                      <LinkIcon className="w-3.5 h-3.5" />
                      {cit.document}
                    </Link>
                  </TableCell>
                  <TableCell className="text-[var(--color-anthracite-400)] text-sm">
                    {cit.format}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" className="text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)]/10">
                        View Analysis
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
