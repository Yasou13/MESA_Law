import React from 'react'
import { StatusBadge } from '../ui/status-badge'
import { Shield, Lock, AlertCircle, FileText, User } from 'lucide-react'

export interface MatterContextHeaderProps {
  matter: {
    name: string
    internal_reference?: string
    client_name?: string
    responsible_attorney_name?: string
    status: string
    confidentiality_level: string
    legal_hold: boolean
    ai_processing_policy: string
  }
}

export function MatterContextHeader({ matter }: MatterContextHeaderProps) {
  return (
    <div className="bg-[var(--bg-surface)] border-b border-[var(--border-surface)] px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl font-bold text-[var(--foreground)]">{matter.name}</h1>
          <StatusBadge status={matter.status === 'open' ? 'success' : 'neutral'} label={matter.status.toUpperCase()} />
          {matter.legal_hold && (
            <StatusBadge status="legal-hold" label="LEGAL HOLD" icon={AlertCircle} />
          )}
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--color-anthracite-500)]">
          {matter.internal_reference && (
            <span className="flex items-center gap-1.5">
              <FileText className="w-4 h-4" /> {matter.internal_reference}
            </span>
          )}
          {matter.client_name && (
            <span className="flex items-center gap-1.5">
              <User className="w-4 h-4" /> {matter.client_name}
            </span>
          )}
          {matter.responsible_attorney_name && (
            <span className="flex items-center gap-1.5">
              <Shield className="w-4 h-4" /> {matter.responsible_attorney_name}
            </span>
          )}
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-2 text-xs font-medium">
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-anthracite-400)] uppercase tracking-wider">Confidentiality:</span>
          <span className="flex items-center gap-1 px-2 py-1 bg-[var(--bg-surface-hover)] rounded-md border border-[var(--border-surface)]">
            <Lock className="w-3.5 h-3.5 text-zinc-500" />
            {matter.confidentiality_level}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[var(--color-anthracite-400)] uppercase tracking-wider">AI Policy:</span>
          <span className="px-2 py-1 bg-[var(--color-lila-50)] text-[var(--color-lila-600)] dark:bg-[var(--color-lila-500)]/10 dark:text-[var(--color-lila-500)] rounded-md border border-[var(--color-lila-500)]/20">
            {matter.ai_processing_policy}
          </span>
        </div>
      </div>
    </div>
  )
}
