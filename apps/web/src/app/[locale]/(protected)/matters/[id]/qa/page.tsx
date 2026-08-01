'use client'

import { use } from 'react'

import { QAShell } from '@/features/qa/components/QAShell'

export default function MatterQAPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ask MESA</h1>
        <p className="mt-1 text-sm text-foreground-secondary">Matter kapsamlı, provenance doğrulamalı hukuki soru-cevap çalışma alanı.</p>
      </div>
      <QAShell matterId={use(params).id} />
    </div>
  )
}
