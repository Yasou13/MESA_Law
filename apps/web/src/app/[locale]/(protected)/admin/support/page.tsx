'use client'

import { useState } from 'react'
import { LifeBuoy, AlertTriangle, Key, Clock, XCircle, CheckCircle2, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function SupportAccessPage() {
  const [accessEnabled, setAccessEnabled] = useState(false)
  const [accessCode, setAccessCode] = useState('')

  const handleGrantAccess = () => {
    setAccessEnabled(true)
    setAccessCode('MESA-SPL-' + Math.random().toString(36).substring(2, 10).toUpperCase())
  }

  const handleRevokeAccess = () => {
    setAccessEnabled(false)
    setAccessCode('')
  }

  return (
    <div className="max-w-4xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Support & Break-Glass</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage temporary access for MESA support engineers.</p>
        </div>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        <div className="p-6 md:p-8 border-b border-[var(--border-surface)]">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500 shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[var(--foreground)]">Support Access Controls</h2>
              <p className="text-[var(--color-anthracite-400)] mt-2 leading-relaxed">
                By default, MESA personnel have <strong>zero access</strong> to your firm's data, matters, or queries. 
                If you encounter a critical issue, you can grant temporary, audited access to a MESA support engineer. 
                All actions taken by support during this window will be logged in the Audit Trail.
              </p>
            </div>
          </div>

          <div className="bg-[var(--bg-surface-hover)] p-6 rounded-xl border border-[var(--border-surface)] space-y-6">
            {!accessEnabled ? (
              <>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium leading-none">Access Duration</label>
                    <Select defaultValue="1">
                      <SelectTrigger className="w-full md:w-[300px] mt-2 bg-[var(--background)]">
                        <SelectValue placeholder="Select duration" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 Hour</SelectItem>
                        <SelectItem value="4">4 Hours</SelectItem>
                        <SelectItem value="24">24 Hours</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium leading-none">Reason for Access</label>
                    <Input placeholder="Ticket number or brief description..." className="mt-2 bg-[var(--background)] max-w-md" />
                  </div>
                </div>
                <div className="pt-4 border-t border-[var(--border-surface)]">
                  <Button onClick={handleGrantAccess} className="gap-2 bg-amber-500 hover:bg-amber-600 text-white">
                    <Key className="w-4 h-4" /> Grant Temporary Access
                  </Button>
                </div>
              </>
            ) : (
              <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
                <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-500">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Support access is currently active</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm text-[var(--color-anthracite-400)]">Provide this code to your support engineer:</label>
                    <div className="mt-2 flex items-center gap-2">
                      <code className="px-4 py-2 bg-[var(--background)] border border-[var(--border-surface)] rounded-lg font-mono text-lg font-bold tracking-widest text-[var(--foreground)]">
                        {accessCode}
                      </code>
                      <Button variant="outline" size="icon" title="Copy code">
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-[var(--color-anthracite-400)]">Access Expires In:</label>
                    <div className="mt-2 flex items-center gap-2 text-[var(--foreground)] font-medium">
                      <Clock className="w-5 h-5 text-amber-500" /> 00:59:45
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-[var(--border-surface)]">
                  <Button onClick={handleRevokeAccess} variant="destructive" className="gap-2">
                    <XCircle className="w-4 h-4" /> Revoke Access Immediately
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="p-6 md:p-8 bg-[var(--bg-surface-hover)]">
          <h3 className="font-semibold text-[var(--foreground)] mb-4 flex items-center gap-2">
            <LifeBuoy className="w-5 h-5 text-[var(--color-lila-500)]" /> Direct Support Options
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-[var(--background)] border border-[var(--border-surface)] rounded-xl">
              <h4 className="font-medium text-[var(--foreground)]">Contact Support</h4>
              <p className="text-sm text-[var(--color-anthracite-400)] mt-1 mb-3">Priority response for Enterprise customers.</p>
              <Button variant="outline" className="w-full text-[var(--color-lila-500)]">support@mesalaw.com</Button>
            </div>
            <div className="p-4 bg-[var(--background)] border border-[var(--border-surface)] rounded-xl">
              <h4 className="font-medium text-[var(--foreground)]">Diagnostic Export</h4>
              <p className="text-sm text-[var(--color-anthracite-400)] mt-1 mb-3">Download anonymized system logs for troubleshooting.</p>
              <Button variant="outline" className="w-full">Download Logs (.zip)</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
