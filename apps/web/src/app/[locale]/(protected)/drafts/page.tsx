'use client'

import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'

import { buttonVariants } from '@/components/ui/button'
import { UnavailableFeature } from '@/components/ui/unavailable-feature'
import { localizedHref, type AppLocale } from '@/lib/navigation'

export default function DraftsPage() {
  const t = useTranslations('DisabledFeature')
  const locale = useLocale() as AppLocale
  return <UnavailableFeature title={t('draftingTitle')} description={t('draftingDescription')} action={<Link href={localizedHref(locale, '/matters')} className={buttonVariants({ variant: 'outline' })}>{t('backToMatters')}</Link>} />
}
