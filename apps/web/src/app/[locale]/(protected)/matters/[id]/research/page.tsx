'use client'

import { use } from 'react'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { ResearchShell } from '@/features/research/components/ResearchShell'

export default function MatterResearchPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  return (
    <div className="h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden flex flex-col">
      <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] shrink-0">
        <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors mb-2">
          <ArrowLeft className="w-4 h-4" /> Back to Matter
        </Link>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">Legal Research</h1>
        <p className="text-sm text-[var(--color-anthracite-500)] mt-1">Deep analysis and case law search grounded in matter evidence.</p>
      </div>

      <div className="flex-1 overflow-hidden p-6 bg-[var(--bg-surface-hover)]">
        <div className="max-w-6xl mx-auto h-full shadow-sm rounded-xl overflow-hidden border border-[var(--border-surface)]">
          {/* Note: In a real integration, we might pass matterId to ResearchShell so it limits context. */}
          <ResearchShell />
        </div>
      </div>
    </div>
  )
}
