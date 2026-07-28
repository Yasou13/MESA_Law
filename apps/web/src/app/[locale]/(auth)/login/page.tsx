'use client'

import { signIn, useSession } from 'next-auth/react'
import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, AlertTriangle, Loader2 } from 'lucide-react'

type AuthState = 'IDLE' | 'SIGNING_IN' | 'REDIRECTING' | 'SESSION_EXPIRED' | 'ACCESS_DENIED' | 'MEMBERSHIP_MISSING' | 'ACCOUNT_DISABLED' | 'IDENTITY_PROVIDER_UNAVAILABLE'

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { status } = useSession()
  const [authState, setAuthState] = useState<AuthState>('IDLE')
  const errorParam = searchParams.get('error')

  useEffect(() => {
    if (errorParam) {
      if (errorParam === 'AccessDenied') setAuthState('ACCESS_DENIED')
      else if (errorParam === 'Configuration') setAuthState('IDENTITY_PROVIDER_UNAVAILABLE')
      else setAuthState('ACCESS_DENIED')
    }
  }, [errorParam])

  useEffect(() => {
    if (status === 'authenticated') {
      setAuthState('REDIRECTING')
      router.push('/dashboard')
    }
  }, [status, router])

  const handleSignIn = async () => {
    setAuthState('SIGNING_IN')
    await signIn('credentials', { callbackUrl: '/dashboard' })
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-[var(--background)]">
      {/* Subtle Background Elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[var(--color-lila-600)]/10 rounded-full mix-blend-screen filter blur-[100px] animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[var(--color-anthracite-600)]/10 rounded-full mix-blend-screen filter blur-[100px] animate-pulse" style={{ animationDelay: '2s' }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md p-8 relative z-10"
      >
        <div className="glass-card rounded-2xl p-10 border border-[var(--border-surface)] shadow-2xl bg-[var(--bg-surface)]/80 backdrop-blur-xl">
          <div className="flex justify-center mb-8">
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
              className="flex items-center justify-center"
            >
              <img src="/icon-192.png" alt="MESA Logo" className="w-16 h-16 rounded-2xl shadow-lg shadow-[var(--color-lila-500)]/20" />
            </motion.div>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-[var(--foreground)] mb-2 tracking-tight">MESA Law</h1>
            <p className="text-[var(--color-anthracite-400)] text-sm">Secure Legal OS</p>
          </div>

          <AnimatePresence mode="wait">
            {['ACCESS_DENIED', 'SESSION_EXPIRED', 'MEMBERSHIP_MISSING', 'ACCOUNT_DISABLED', 'IDENTITY_PROVIDER_UNAVAILABLE'].includes(authState) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-6 p-4 rounded-xl bg-[var(--color-semantic-error)]/10 border border-[var(--color-semantic-error)]/20 flex items-start gap-3"
              >
                <AlertTriangle className="w-5 h-5 text-[var(--color-semantic-error)] flex-shrink-0 mt-0.5" />
                <div className="text-sm text-[var(--color-semantic-error)]">
                  {authState === 'ACCESS_DENIED' && 'Access denied. You do not have permission to access this application.'}
                  {authState === 'SESSION_EXPIRED' && 'Your session has expired. Please sign in again.'}
                  {authState === 'MEMBERSHIP_MISSING' && 'No active firm membership found for this account.'}
                  {authState === 'ACCOUNT_DISABLED' && 'This account has been disabled by the administrator.'}
                  {authState === 'IDENTITY_PROVIDER_UNAVAILABLE' && 'The authentication provider is currently unavailable.'}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="space-y-4">
            <button
              onClick={handleSignIn}
              disabled={authState === 'SIGNING_IN' || authState === 'REDIRECTING' || status === 'loading'}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] text-white border border-[var(--border-surface)] rounded-xl font-medium transition-all hover:scale-[1.02] active:scale-95 shadow-sm disabled:opacity-50 disabled:pointer-events-none disabled:scale-100"
            >
              {authState === 'SIGNING_IN' || authState === 'REDIRECTING' || status === 'loading' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {authState === 'REDIRECTING' ? 'Redirecting...' : 'Signing in...'}
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5 opacity-90" />
                  Sign in (Dev Mode)
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--background)] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[var(--color-lila-500)]" /></div>}>
      <LoginContent />
    </Suspense>
  )
}
