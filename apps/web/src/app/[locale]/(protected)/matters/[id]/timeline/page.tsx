'use client'

import { useTranslations } from 'next-intl'
import { use } from 'react'

import { DegradedState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel, PanelBody } from '@/components/ui/panel'
import { Timeline } from '@/features/matters/components/Timeline'

export default function MatterTimelinePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: matterId } = use(params)
  const t = useTranslations('Timeline')

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />
      <DegradedState title={t('confidence')} description={t('dateQualityUnavailable')} />
      <Panel><PanelBody><Timeline matterId={matterId} /></PanelBody></Panel>
    </div>
  )
}
