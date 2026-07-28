'use client'

import { use } from 'react'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { Timeline } from '@/features/matters/components/Timeline'

export default function MatterTimelinePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  return (
    <div className="max-w-5xl mx-auto p-6 lg:p-8 space-y-8">
      <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Matter Overview
      </Link>
      
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Matter Timeline</h1>
        <p className="text-[var(--color-anthracite-500)] mt-1">Chronological view of all extracted events and facts.</p>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] p-2">
        <Timeline matterId={matterId} />
      </div>
    </div>
  )
}
