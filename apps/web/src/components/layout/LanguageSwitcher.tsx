'use client'

import { Globe } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { usePathname, useRouter } from 'next/navigation'

import { locales } from '@/i18n'

export function LanguageSwitcher() {
  const locale = useLocale()
  const t = useTranslations('Shell')
  const router = useRouter()
  const pathname = usePathname()

  const handleLocaleChange = (newLocale: string) => {
    if (newLocale === locale) return
    const segments = pathname.split('/')
    if (locales.includes(segments[1] as (typeof locales)[number])) segments.splice(1, 1)
    const path = segments.join('/') || '/'
    router.replace(newLocale === 'tr' ? path : `/${newLocale}${path}`)
    router.refresh()
  }

  return (
    <label className="flex h-9 items-center gap-1 rounded-md px-2 text-foreground-secondary hover:bg-surface-subtle">
      <Globe className="size-4" aria-hidden="true" /><span className="sr-only">{t('language')}</span>
      <select value={locale} onChange={(event) => handleLocaleChange(event.target.value)} className="cursor-pointer border-0 bg-transparent text-xs font-medium text-foreground outline-none">
        <option value="tr">TR</option><option value="en">EN</option>
      </select>
    </label>
  )
}
