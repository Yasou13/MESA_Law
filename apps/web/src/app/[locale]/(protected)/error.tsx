'use client'

import { AlertOctagon, Home, RotateCcw } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { useEffect } from 'react'

import { Button, buttonVariants } from '@/components/ui/button'
import { Panel, PanelBody } from '@/components/ui/panel'
import { localizedHref, type AppLocale } from '@/lib/navigation'

export default function ErrorBoundary({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations('ErrorBoundary')
  const locale = useLocale() as AppLocale
  useEffect(() => { console.error(error) }, [error])
  return (
    <div className="flex min-h-[60vh] items-center justify-center py-8">
      <Panel className="w-full max-w-lg border-danger/30"><PanelBody className="flex flex-col items-center p-7 text-center">
        <span className="flex size-12 items-center justify-center rounded-full bg-danger-soft text-danger"><AlertOctagon className="size-6" /></span>
        <h1 className="mt-5 text-xl font-semibold">{t('title')}</h1><p className="mt-2 text-sm leading-6 text-foreground-secondary">{t('description')}</p>
        <pre className="mt-5 max-h-32 w-full overflow-auto whitespace-pre-wrap break-all rounded-md bg-surface-subtle p-3 text-left text-xs text-danger">{error.message || t('unknown')}{error.digest && `\nDigest: ${error.digest}`}</pre>
        <div className="mt-6 flex flex-wrap justify-center gap-2"><Button onClick={reset}><RotateCcw className="size-4" />{t('tryAgain')}</Button><Link href={localizedHref(locale, '/dashboard')} className={buttonVariants({ variant: 'outline' })}><Home className="size-4" />{t('dashboard')}</Link></div>
      </PanelBody></Panel>
    </div>
  )
}
