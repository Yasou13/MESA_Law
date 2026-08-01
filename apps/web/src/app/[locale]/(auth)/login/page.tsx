'use client'

import { AlertTriangle, Loader2, ShieldCheck } from 'lucide-react'
import { signIn, useSession } from 'next-auth/react'
import { useLocale, useTranslations } from 'next-intl'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { localizedHref, type AppLocale } from '@/lib/navigation'

type AuthState = 'IDLE' | 'SIGNING_IN' | 'REDIRECTING' | 'SESSION_EXPIRED' | 'ACCESS_DENIED' | 'MEMBERSHIP_MISSING' | 'ACCOUNT_DISABLED' | 'IDENTITY_PROVIDER_UNAVAILABLE'

function LoginContent() {
  const t = useTranslations('Login')
  const locale = useLocale() as AppLocale
  const router = useRouter()
  const searchParams = useSearchParams()
  const { status } = useSession()
  const [authState, setAuthState] = useState<AuthState>('IDLE')
  const dashboardHref = localizedHref(locale, '/dashboard')

  useEffect(() => {
    const error = searchParams.get('error')
    if (error === 'Configuration') setAuthState('IDENTITY_PROVIDER_UNAVAILABLE')
    else if (error) setAuthState('ACCESS_DENIED')
  }, [searchParams])

  useEffect(() => {
    if (status !== 'authenticated') return
    setAuthState('REDIRECTING')
    router.push(dashboardHref)
  }, [dashboardHref, router, status])

  const errorMessage = authState === 'ACCESS_DENIED' ? t('accessDenied')
    : authState === 'SESSION_EXPIRED' ? t('sessionExpired')
      : authState === 'MEMBERSHIP_MISSING' ? t('membershipMissing')
        : authState === 'ACCOUNT_DISABLED' ? t('accountDisabled')
          : authState === 'IDENTITY_PROVIDER_UNAVAILABLE' ? t('providerUnavailable')
            : null

  const pending = authState === 'SIGNING_IN' || authState === 'REDIRECTING' || status === 'loading'

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4">
      <div className="absolute right-4 top-4"><ThemeToggle /></div>
      <main className="w-full max-w-md rounded-lg border border-border bg-surface p-7 shadow-md sm:p-9">
        <div className="flex items-center gap-4">
          <img src="/icon-192.png" alt="MESA" className="size-12 rounded-md" />
          <div><h1 className="text-2xl font-semibold tracking-tight">MESA Law</h1><p className="mt-1 text-sm text-foreground-secondary">{t('tagline')}</p></div>
        </div>

        {errorMessage && (
          <div className="mt-6 flex gap-3 rounded-md border border-danger/30 bg-danger-soft p-4 text-sm text-danger" role="alert">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" /><p>{errorMessage}</p>
          </div>
        )}

        <Button
          className="mt-7 h-11 w-full"
          disabled={pending}
          onClick={async () => { setAuthState('SIGNING_IN'); await signIn('keycloak', { callbackUrl: dashboardHref }) }}
        >
          {pending ? <Loader2 className="size-5 animate-spin" /> : <ShieldCheck className="size-5" />}
          {authState === 'REDIRECTING' ? t('redirecting') : pending ? t('signingIn') : t('signIn')}
        </Button>
        <p className="mt-5 text-center text-xs leading-5 text-foreground-muted">Keycloak · OpenID Connect</p>
      </main>
    </div>
  )
}

export default function LoginPage() {
  return <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-background"><Loader2 className="size-8 animate-spin text-primary-content" /></div>}><LoginContent /></Suspense>
}
