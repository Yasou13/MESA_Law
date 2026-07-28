'use client'

import { use, useState } from 'react'
import { ArrowLeft, MessageSquare, Plus, Clock } from 'lucide-react'
import Link from 'next/link'
import { QAShell } from '@/features/qa/components/QAShell'

export default function MatterQAPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden w-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-4 border-b border-[var(--border-surface)] flex items-center justify-between">
          <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Matter
          </Link>
          <div className="flex items-center gap-2 text-sm text-[var(--color-anthracite-500)]">
            <Clock className="w-4 h-4" /> Session active
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[var(--bg-surface-hover)]">
          <div className="max-w-4xl mx-auto w-full space-y-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Matter Q&A</h1>
              <p className="text-[var(--color-anthracite-500)] mt-1">Ask questions about this matter based on the evidence and timeline.</p>
            </div>
            
            <div className="h-[650px] shadow-sm rounded-xl overflow-hidden border border-[var(--border-surface)]">
              <QAShell matterId={matterId} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
