'use client'

import { useState } from 'react'
import { Lock, FileWarning, Search, Filter, ShieldAlert, FileClock, Scale, Trash2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'
import { formatDistanceToNow } from 'date-fns'

// UI Stub for Phase 31
const mockHolds = [
  { id: 'hold_01', matter: 'Smith v. Jones (IP Dispute)', type: 'Ligation Hold', scope: 'All Matter Documents & Emails', appliedBy: 'Jane Doe', appliedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(), status: 'active' },
  { id: 'hold_02', matter: 'TechCorp Merger', type: 'Regulatory Hold', scope: 'Financial Records', appliedBy: 'System', appliedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(), status: 'active' },
  { id: 'hold_03', matter: 'Estate of M. Robert', type: 'Preservation Order', scope: 'Personal Correspondence', appliedBy: 'John Smith', appliedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 365).toISOString(), status: 'released' },
]

export default function RetentionPage() {
  const [search, setSearch] = useState('')
  const [holds] = useState(mockHolds)
  
  const filteredHolds = holds.filter(h => 
    h.matter.toLowerCase().includes(search.toLowerCase()) || 
    h.type.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Legal Holds & Retention</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage data preservation orders and automated deletion policies.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <FileClock className="w-4 h-4" /> Global Retention Policy
          </Button>
          <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
            <Plus className="w-4 h-4" /> New Legal Hold
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="glass-card p-5 rounded-xl border border-[var(--color-semantic-warning)]/30 bg-[var(--color-semantic-warning)]/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Lock className="w-5 h-5 text-[var(--color-semantic-warning)]" />
            <h3 className="font-medium text-[var(--color-semantic-warning)]">Active Holds</h3>
          </div>
          <p className="text-2xl font-bold text-[var(--foreground)]">24</p>
          <p className="text-sm text-[var(--color-anthracite-400)] mt-1">Matters locked from deletion</p>
        </div>
        <div className="glass-card p-5 rounded-xl border border-[var(--border-surface)] shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <FileWarning className="w-5 h-5 text-[var(--color-anthracite-400)]" />
            <h3 className="font-medium text-[var(--color-anthracite-300)]">Pending Deletions</h3>
          </div>
          <p className="text-2xl font-bold text-[var(--foreground)]">1,245</p>
          <p className="text-sm text-[var(--color-anthracite-400)] mt-1">Documents aging out this week</p>
        </div>
        <div className="glass-card p-5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <ShieldAlert className="w-5 h-5 text-emerald-500" />
            <h3 className="font-medium text-emerald-500">Compliance Status</h3>
          </div>
          <p className="text-2xl font-bold text-[var(--foreground)]">100%</p>
          <p className="text-sm text-[var(--color-anthracite-400)] mt-1">All retention policies met</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search holds or matters..."
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
        {filteredHolds.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Scale className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Legal Holds</h3>
            <p className="text-[var(--color-anthracite-500)]">There are no preservation orders matching your criteria.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>Matter</TableHead>
                <TableHead>Hold Type & Scope</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Applied By</TableHead>
                <TableHead>Age</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredHolds.map(hold => (
                <TableRow key={hold.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell className="font-medium text-[var(--foreground)]">
                    {hold.matter}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <span className="font-medium text-[var(--foreground)]">{hold.type}</span>
                      <span className="text-xs text-[var(--color-anthracite-400)]">{hold.scope}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge 
                      status={hold.status === 'active' ? 'warning' : 'default'} 
                      label={hold.status === 'active' ? 'ACTIVE HOLD' : 'RELEASED'} 
                    />
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-400)]">
                    {hold.appliedBy}
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-500)]">
                    {formatDistanceToNow(new Date(hold.appliedAt))}
                  </TableCell>
                  <TableCell className="text-right">
                    {hold.status === 'active' ? (
                      <Button variant="ghost" size="sm" className="text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)]/10">
                        Manage Hold
                      </Button>
                    ) : (
                      <Button variant="ghost" size="sm" className="text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]">
                        View Log
                      </Button>
                    )}
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
