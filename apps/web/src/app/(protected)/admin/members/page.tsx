'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Users, Mail, Shield, MoreVertical } from 'lucide-react'

export default function MembersPage() {
  const { data: members, isLoading } = useQuery({
    queryKey: ['members'],
    queryFn: async () => {
      // Mocking for now since there's no backend endpoint yet
      return [
        { id: 1, name: 'Alice Lawyer', email: 'alice@firm.com', role: 'admin', status: 'active' },
        { id: 2, name: 'Bob Partner', email: 'bob@firm.com', role: 'member', status: 'active' },
        { id: 3, name: 'Charlie Associate', email: 'charlie@firm.com', role: 'member', status: 'invited' },
      ]
    }
  })

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[var(--foreground)] flex items-center gap-2">
            <Users className="w-6 h-6 text-[var(--color-lila-500)]" />
            Organization Members
          </h1>
          <p className="text-[var(--color-anthracite-400)] mt-1">Manage firm attorneys, paralegals, and their access levels.</p>
        </div>
        <button className="bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors shadow-sm">
          Invite Member
        </button>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl overflow-hidden shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="bg-[var(--bg-surface-hover)] text-[var(--color-anthracite-400)] text-xs uppercase font-semibold border-b border-[var(--border-surface)]">
            <tr>
              <th className="px-6 py-4">User</th>
              <th className="px-6 py-4">Role</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-surface)]">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-[var(--color-anthracite-400)]">
                  Loading members...
                </td>
              </tr>
            ) : members?.map((member) => (
              <tr key={member.id} className="hover:bg-[var(--bg-surface-hover)] transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-[var(--color-lila-500)]/10 text-[var(--color-lila-500)] flex items-center justify-center font-bold">
                      {member.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium text-[var(--foreground)]">{member.name}</div>
                      <div className="text-[var(--color-anthracite-400)] flex items-center gap-1 mt-0.5">
                        <Mail className="w-3 h-3" />
                        {member.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1.5 text-[var(--foreground)]">
                    {member.role === 'admin' ? <Shield className="w-4 h-4 text-[var(--color-semantic-warning)]" /> : <Users className="w-4 h-4 text-[var(--color-anthracite-400)]" />}
                    <span className="capitalize">{member.role}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                    member.status === 'active' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {member.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="p-1.5 text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)] rounded transition-colors">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
