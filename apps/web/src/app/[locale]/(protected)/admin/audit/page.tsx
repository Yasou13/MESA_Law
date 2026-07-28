'use client'

import { useState } from 'react'
import { ShieldCheck, Search, Filter, Download, Activity, FileText, User, ArrowUpRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'

import { useListAuditEvents } from '@/api/endpoints/audit/audit'

export default function AuditPage() {
  const [search, setSearch] = useState('')
  const { data: res, isLoading } = useListAuditEvents()
  const logs = (res as unknown as any[]) || []
  
  const filteredLogs = logs.filter((l: any) => 
    (l.user_id && l.user_id.toLowerCase().includes(search.toLowerCase())) || 
    l.action.toLowerCase().includes(search.toLowerCase()) ||
    l.entity_type.toLowerCase().includes(search.toLowerCase())
  )

  const getActionColor = (action: string) => {
    if (action.includes('DELETE') || action.includes('REMOVE')) return 'text-[var(--color-semantic-error)] bg-[var(--color-semantic-error)]/10 border-[var(--color-semantic-error)]/20'
    if (action.includes('EXPORT') || action.includes('DOWNLOAD')) return 'text-amber-500 bg-amber-500/10 border-amber-500/20'
    if (action.includes('RUN') || action.includes('AI')) return 'text-[var(--color-lila-500)] bg-[var(--color-lila-500)]/10 border-[var(--color-lila-500)]/20'
    return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Audit Logs</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Monitor all user activities, data exports, and system events for compliance.</p>
        </div>
        <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
          <Download className="w-4 h-4" /> Export CSV
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search by user, action, or matter..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 w-full"
          />
        </div>
        <Button variant="outline" className="gap-2 shrink-0">
          <Filter className="w-4 h-4" /> Filter Events
        </Button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <ShieldCheck className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Audit Records</h3>
            <p className="text-[var(--color-anthracite-500)]">No logs match your search criteria.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>User / Principal</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Context / Matter</TableHead>
                <TableHead>Target Resource</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead className="text-right">Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map(log => (
                <TableRow key={log.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-[var(--color-anthracite-800)] flex items-center justify-center text-white shrink-0">
                        {log.user_id ? <User className="w-3 h-3" /> : <Activity className="w-3 h-3" />}
                      </div>
                      <span className="font-medium text-[var(--foreground)] font-mono text-xs max-w-[150px] truncate">{log.user_id || 'System'}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 text-[10px] font-bold uppercase tracking-wider rounded border ${getActionColor(log.action)}`}>
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-400)] uppercase font-semibold text-xs">
                    {log.entity_type}
                  </TableCell>
                  <TableCell className="text-xs font-mono text-[var(--foreground)] truncate max-w-[200px]">
                    {log.entity_id}
                  </TableCell>
                  <TableCell className="text-sm text-[var(--color-anthracite-500)]">
                    <div title={new Date(log.timestamp).toLocaleString()}>
                      {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)] gap-1">
                      View <ArrowUpRight className="w-3 h-3" />
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
