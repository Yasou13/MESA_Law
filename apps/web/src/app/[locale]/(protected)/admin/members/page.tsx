'use client'

import { useListFirmMembers } from '@/api/endpoints/default/default'
import { Users, Shield, User as UserIcon, Loader2, AlertCircle, Edit, MoreHorizontal, Mail } from 'lucide-react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'


export default function MembersPage() {
  const { data: membersRes, isLoading, isError } = useListFirmMembers()
  const members = (membersRes?.data as any[]) || []

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Organization Members</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage access and roles for your firm.</p>
        </div>
        <Button className="gap-2">
          <Mail className="w-4 h-4" /> Invite Member
        </Button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <Loader2 className="animate-spin h-8 w-8 text-[var(--color-lila-500)]" />
            <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading members...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <AlertCircle className="w-12 h-12 text-[var(--color-semantic-error)]" />
            <h3 className="text-xl font-bold text-[var(--foreground)]">Failed to load members</h3>
            <p className="text-[var(--color-anthracite-500)]">Please try again later.</p>
          </div>
        ) : members.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 border-dashed border-2 border-[var(--border-surface)] m-4 rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Users className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No Members Found</h3>
            <p className="text-[var(--color-anthracite-500)]">Invite colleagues to your firm to get started.</p>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-[var(--bg-surface-hover)]">
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((member: any) => (
                <TableRow key={member.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[var(--bg-surface)] border border-[var(--border-surface)] flex items-center justify-center shrink-0 text-[var(--color-lila-500)] font-bold">
                        {member.full_name?.charAt(0)?.toUpperCase() || <UserIcon className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="font-medium text-[var(--foreground)]">{member.full_name || 'Unnamed User'}</div>
                        <div className="text-sm text-[var(--color-anthracite-500)]">{member.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 text-sm text-[var(--color-anthracite-400)]">
                      {member.role === 'admin' ? (
                        <Shield className="w-4 h-4 text-[var(--color-lila-500)]" />
                      ) : (
                        <UserIcon className="w-4 h-4" />
                      )}
                      <span className="capitalize">{member.role}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge 
                      status={member.is_active ? 'success' : 'error'} 
                      label={member.is_active ? 'ACTIVE' : 'INACTIVE'} 
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="icon-sm" title="Edit Role">
                        <Edit className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                      </Button>
                      <Button variant="ghost" size="icon-sm" className="text-red-500 hover:text-red-600 hover:bg-red-500/10" title="Deactivate User">
                        <AlertCircle className="w-4 h-4" />
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
