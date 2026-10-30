'use client'

import {
  AlertCircle,
  Eye,
  EyeOff,
  Lock,
  Scale,
  ShieldCheck,
  User,
  Loader2,
  ArrowRight,
} from 'lucide-react'
import { signIn, useSession } from 'next-auth/react'
import { useLocale, useTranslations } from 'next-intl'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { localizedHref, type AppLocale } from '@/lib/navigation'

type AuthState =
  | 'IDLE'
  | 'SIGNING_IN'
  | 'REDIRECTING'
  | 'INVALID_CREDENTIALS'
  | 'SESSION_EXPIRED'
  | 'ACCESS_DENIED'
  | 'MEMBERSHIP_MISSING'
  | 'ACCOUNT_DISABLED'
  | 'IDENTITY_PROVIDER_UNAVAILABLE'

function LoginContent() {
  const t = useTranslations('Login')
  const locale = useLocale() as AppLocale
  const router = useRouter()
  const searchParams = useSearchParams()
  const { status } = useSession()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [authState, setAuthState] = useState<AuthState>('IDLE')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const dashboardHref = localizedHref(locale, '/dashboard')

  useEffect(() => {
    const error = searchParams.get('error')
    if (error === 'Configuration') {
      setAuthState('IDENTITY_PROVIDER_UNAVAILABLE')
      setErrorMessage(t('providerUnavailable'))
    } else if (error === 'CredentialsSignin') {
      setAuthState('INVALID_CREDENTIALS')
      setErrorMessage(t('invalidCredentials'))
    } else if (error) {
      setAuthState('ACCESS_DENIED')
      setErrorMessage(t('accessDenied'))
    }
  }, [searchParams, t])

  useEffect(() => {
    if (status !== 'authenticated') return
    setAuthState('REDIRECTING')
    router.push(dashboardHref)
  }, [dashboardHref, router, status])

  const pending =
    authState === 'SIGNING_IN' ||
    authState === 'REDIRECTING' ||
    status === 'loading'

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) return

    setAuthState('SIGNING_IN')
    setErrorMessage(null)

    try {
      const result = await signIn('keycloak-credentials', {
        redirect: false,
        username: username.trim(),
        password,
      })

      if (!result || result.error) {
        setAuthState('INVALID_CREDENTIALS')
        setErrorMessage(t('invalidCredentials'))
      } else if (result.ok) {
        setAuthState('REDIRECTING')
        router.push(dashboardHref)
      }
    } catch {
      setAuthState('IDENTITY_PROVIDER_UNAVAILABLE')
      setErrorMessage(t('providerUnavailable'))
    }
  }

  const handleKeycloakSSO = async () => {
    setAuthState('SIGNING_IN')
    setErrorMessage(null)
    await signIn('keycloak', { callbackUrl: dashboardHref })
  }

  return (
    <div className="relative min-h-screen w-full bg-background flex flex-col lg:grid lg:grid-cols-12 overflow-x-hidden">
      {/* ── Left Hero Panel (Decorative & Legal Highlights) ── */}
      <div className="relative hidden lg:flex lg:col-span-6 xl:col-span-7 flex-col justify-between overflow-hidden bg-gradient-to-br from-[#070e1b] via-[#0d1c33] to-[#152a48] p-12 text-white">
        {/* Subtle geometric & radial glow background */}
        <div className="pointer-events-none absolute -left-20 -top-20 size-[500px] rounded-full bg-blue-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -right-20 size-[500px] rounded-full bg-indigo-500/10 blur-3xl" />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)`,
            backgroundSize: '24px 24px',
          }}
        />

        {/* Brand Header */}
        <div className="relative z-10 flex items-center gap-3.5">
          <div className="relative flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-400 to-indigo-600 shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
            <Scale className="size-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white font-serif">
              MESA<span className="text-blue-400 ml-1">LAW</span>
            </span>
            <span className="block text-[11px] font-medium uppercase tracking-widest text-blue-200/70">
              Legal Operating System
            </span>
          </div>
        </div>

        {/* Minimalist Center Showcase */}
        <div className="relative z-10 my-auto flex flex-col items-center justify-center text-center py-16">
          <div className="relative flex size-24 items-center justify-center rounded-3xl bg-white/[0.04] border border-white/10 shadow-2xl shadow-blue-500/10 backdrop-blur-xl">
            <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-500/20 via-transparent to-indigo-500/20 blur-xl" />
            <Scale className="relative size-12 text-blue-300/90" strokeWidth={1.5} />
          </div>
          <p className="mt-5 text-xs font-medium tracking-widest uppercase text-blue-200/50">
            Legal Operating System
          </p>
        </div>

        {/* Hero Footer */}
        <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-6 text-xs text-blue-200/60">
          <span>© {new Date().getFullYear()} MESA Law</span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-emerald-400" />
            <span>Keycloak OIDC · Multi-Tenant Architecture</span>
          </span>
        </div>
      </div>

      {/* ── Right Form Column ── */}
      <div className="relative flex flex-1 lg:col-span-6 xl:col-span-5 flex-col justify-between p-6 sm:p-10 lg:p-12 xl:p-16">
        {/* Top Control Bar */}
        <div className="flex items-center justify-between">
          {/* Mobile-only logo */}
          <div className="flex lg:hidden items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Scale className="size-4" />
            </div>
            <span className="font-serif font-bold text-lg tracking-tight">
              MESA<span className="text-primary ml-0.5">LAW</span>
            </span>
          </div>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>

        {/* Center Auth Card */}
        <main className="mx-auto w-full max-w-sm sm:max-w-md my-auto py-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-foreground font-serif">
              {t('title')}
            </h1>
            <p className="mt-2 text-sm text-foreground-secondary leading-normal">
              {t('subtitle')}
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div
              className="mt-6 flex items-start gap-3 rounded-lg border border-danger/30 bg-danger-soft p-3.5 text-sm text-danger animate-in fade-in-50 duration-200"
              role="alert"
            >
              <AlertCircle className="size-5 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
            </div>
          )}

          {/* Direct Credentials Login Form */}
          <form onSubmit={handleCredentialsSubmit} className="mt-7 space-y-4">
            {/* Username / Email Field */}
            <div className="space-y-1.5">
              <label
                htmlFor="username"
                className="block text-xs font-semibold uppercase tracking-wider text-foreground-secondary"
              >
                {t('usernameLabel')}
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-foreground-muted" />
                <Input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  placeholder={t('usernamePlaceholder')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={pending}
                  className="pl-10 h-11 bg-surface border-border text-sm"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold uppercase tracking-wider text-foreground-secondary"
                >
                  {t('passwordLabel')}
                </label>
                <button
                  type="button"
                  tabIndex={-1}
                  className="text-xs text-primary hover:text-primary-hover hover:underline transition-colors font-medium"
                  onClick={() => alert('Şifre sıfırlama talebiniz için sistem yöneticiniz veya Keycloak admini ile iletişime geçiniz.')}
                >
                  {t('forgotPassword')}
                </button>
              </div>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-foreground-muted" />
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  placeholder={t('passwordPlaceholder')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={pending}
                  className="pl-10 pr-10 h-11 bg-surface border-border text-sm"
                />
                <button
                  type="button"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Şifreyi gizle' : 'Şifreyi göster'}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-foreground-muted hover:text-foreground transition-colors p-1"
                >
                  {showPassword ? (
                    <EyeOff className="size-4" />
                  ) : (
                    <Eye className="size-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center space-x-2.5 pt-1">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(c) => setRememberMe(c === true)}
                disabled={pending}
              />
              <label
                htmlFor="remember"
                className="text-xs font-medium text-foreground-secondary select-none cursor-pointer"
              >
                {t('rememberMe')}
              </label>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="mt-2 h-11 w-full bg-primary hover:bg-primary-hover active:bg-primary-active text-primary-foreground shadow-sm hover:shadow transition-all font-medium text-sm gap-2"
              disabled={pending || !username.trim() || !password}
            >
              {pending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  <span>{authState === 'REDIRECTING' ? t('redirecting') : t('signingIn')}</span>
                </>
              ) : (
                <>
                  <span>{t('signIn')}</span>
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-7 flex items-center justify-center">
            <div className="w-full border-t border-border" />
            <span className="absolute bg-background px-3 text-[11px] uppercase tracking-wider text-foreground-muted">
              {t('orContinueWith')}
            </span>
          </div>

          {/* Secondary Keycloak Direct SSO Button (Keeps e2e & SSO flow compatible) */}
          <Button
            type="button"
            variant="outline"
            className="h-11 w-full border-border bg-surface hover:bg-surface-subtle text-foreground text-sm font-medium gap-2.5 transition-colors"
            disabled={pending}
            onClick={handleKeycloakSSO}
          >
            <ShieldCheck className="size-4 text-primary" />
            <span>{t('signInWithKeycloak')}</span>
          </Button>

          {/* Footer Security Note */}
          <p className="mt-8 text-center text-xs leading-relaxed text-foreground-muted">
            {t('securityBadge')}
          </p>
        </main>

        {/* Bottom copyright on mobile/tablet */}
        <div className="text-center text-[11px] text-foreground-muted lg:hidden pt-4">
          © {new Date().getFullYear()} MESA Law · Tüm hakları saklıdır.
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <Loader2 className="size-8 animate-spin text-primary" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  )
}
