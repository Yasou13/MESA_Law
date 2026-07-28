'use client'

import { useState } from 'react'
import { Activity, Clock, PlayCircle, CheckCircle2, AlertCircle, RotateCw, Filter, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'
import { formatDistanceToNow } from 'date-fns'

// UI Stub for Phase 27
const mockJobs = [
  { id: 'job_48291a', type: 'Legal Research Deep Scan', matter: 'Smith v. Jones (IP Dispute)', status: 'processing', progress: 65, startedAt: new Date(Date.now() - 1000 * 60 * 5).toISOString() },
  { id: 'job_48291b', type: 'Batch Document OCR', matter: 'TechCorp Merger', status: 'completed', progress: 100, startedAt: new Date(Date.now() - 1000 * 60 * 45).toISOString() },
  { id: 'job_48291c', type: 'Citation Verification', matter: 'Smith v. Jones (IP Dispute)', status: 'failed', progress: 30, startedAt: new Date(Date.now() - 1000 * 60 * 120).toISOString(), error: 'Timeout waiting for external database.' },
  { id: 'job_48291d', type: 'Extract Claims & Defenses', matter: 'Estate of M. Robert', status: 'queued', progress: 0, startedAt: new Date(Date.now() - 1000 * 60 * 1).toISOString() },
]

export default function OperationsPage() {
  const [search, setSearch] = useState('')
  const [jobs] = useState(mockJobs)
  
  const filteredJobs = jobs.filter(j => 
    j.type.toLowerCase().includes(search.toLowerCase()) || 
    j.matter.toLowerCase().includes(search.toLowerCase()) ||
    j.id.toLowerCase().includes(search.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'processing': return <RotateCw className="w-4 h-4 text-amber-500 animate-spin" />
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'queued': return <Clock className="w-4 h-4 text-[var(--color-anthracite-400)]" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">System Operations</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Monitor background tasks, data extractions, and research jobs.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <RotateCw className="w-4 h-4" /> Refresh
          </Button>
          <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
            <PlayCircle className="w-4 h-4" /> Start Manual Job
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-4 rounded-xl border border-[var(--border-surface)] shadow-sm">
          <div className="text-sm font-medium text-[var(--color-anthracite-400)]">Total Jobs (24h)</div>
          <div className="text-2xl font-bold mt-1 text-[var(--foreground)]">128</div>
        </div>
        <div className="glass-card p-4 rounded-xl border border-[var(--color-lila-500)]/30 bg-[var(--color-lila-500)]/5 shadow-sm">
          <div className="text-sm font-medium text-[var(--color-lila-500)]">Processing</div>
          <div className="text-2xl font-bold mt-1 text-[var(--color-lila-400)]">1</div>
        </div>
        <div className="glass-card p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 shadow-sm">
          <div className="text-sm font-medium text-emerald-500">Completed</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">124</div>
        </div>
        <div className="glass-card p-4 rounded-xl border border-[var(--color-semantic-error)]/30 bg-[var(--color-semantic-error)]/5 shadow-sm">
          <div className="text-sm font-medium text-[var(--color-semantic-error)]">Failed</div>
          <div className="text-2xl font-bold mt-1 text-[var(--color-semantic-error)]">3</div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search by Job ID, type, or matter..."
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
        {filteredJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Activity className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Jobs Found</h3>
            <p className="text-[var(--color-anthracite-500)]">There are no background operations matching your criteria.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>Job ID & Type</TableHead>
                <TableHead>Matter context</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Started</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredJobs.map(job => (
                <TableRow key={job.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="mt-0.5">{getStatusIcon(job.status)}</div>
                      <div>
                        <div className="font-medium text-[var(--foreground)]">{job.type}</div>
                        <div className="text-xs text-[var(--color-anthracite-500)] font-mono">{job.id}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-400)]">
                    {job.matter}
                  </TableCell>
                  <TableCell>
                    <StatusBadge 
                      status={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'error' : job.status === 'processing' ? 'processing' : 'default'} 
                      label={job.status.toUpperCase()} 
                    />
                    {job.error && (
                      <div className="text-xs text-[var(--color-semantic-error)] mt-1 max-w-[200px] truncate" title={job.error}>
                        {job.error}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="w-full max-w-[150px]">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[var(--color-anthracite-400)]">{job.progress}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-[var(--bg-surface-hover)] rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${
                            job.status === 'completed' ? 'bg-emerald-500' :
                            job.status === 'failed' ? 'bg-[var(--color-semantic-error)]' :
                            'bg-[var(--color-lila-500)]'
                          }`}
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-500)]">
                    {formatDistanceToNow(new Date(job.startedAt), { addSuffix: true })}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)]">
                      View Logs
                    </Button>
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
