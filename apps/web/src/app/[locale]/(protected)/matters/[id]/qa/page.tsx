'use client'

import { use } from 'react'
import { useTranslations } from 'next-intl'

import { QAShell } from '@/features/qa/components/QAShell'

export default function MatterQAPage({ params }: { params: Promise<{ id: string }> }) {
  const t = useTranslations('AskMesaEntry')
  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('title')}</h1>
        <p className="mt-1 text-sm text-foreground-secondary">{t('workspaceDescription')}</p>
      </div>
      <QAShell matterId={use(params).id} />
    </div>
  )
}
