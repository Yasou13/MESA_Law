'use client'

import { useListFirmMembers } from '@/api/endpoints/default/default'
import { Users, Shield, User as UserIcon } from 'lucide-react'

export default function MembersPage() {
  const { data: membersRes, isLoading, isError } = useListFirmMembers()
  const members = (membersRes?.data as any[]) || []

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Organization Members</h1>
          <p className="text-zinc-400">Manage access and roles for your firm.</p>
        </div>
        <button className="px-4 py-2 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors text-sm font-medium">
          Invite Member
        </button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {isLoading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
          </div>
        )}

        {!isLoading && !isError && (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--border-surface)] text-sm font-medium text-zinc-400 uppercase tracking-wider">
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-surface)]">
              {members.map((member: any) => (
                <tr key={member.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[var(--bg-surface)] flex items-center justify-center shrink-0 text-[var(--color-lila-400)] font-medium">
                        {member.full_name?.charAt(0) || <UserIcon className="w-4 h-4" />}
                      </div>
                      <div>
                        <div className="font-medium text-[var(--foreground)]">{member.full_name}</div>
                        <div className="text-sm text-zinc-400">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5 text-sm">
                      {member.role === 'admin' ? (
                        <Shield className="w-4 h-4 text-[var(--color-lila-400)]" />
                      ) : (
                        <UserIcon className="w-4 h-4 text-zinc-400" />
                      )}
                      <span className="capitalize">{member.role}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      member.is_active 
                        ? 'bg-emerald-500/10 text-emerald-500' 
                        : 'bg-red-500/10 text-red-500'
                    }`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-sm text-[var(--color-lila-400)] hover:text-[var(--color-lila-300)] font-medium">
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
              {members.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-zinc-400">
                    <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    No members found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
