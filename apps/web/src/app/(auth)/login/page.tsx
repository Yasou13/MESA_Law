'use client'

import { signIn, useSession } from 'next-auth/react'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const { status } = useSession()

  useEffect(() => {
    // Phase 1: MESA Law requires deriving tenant natively from session.
    // Tenant context is no longer injected by localStorage.
    if (status === 'authenticated') {
      router.push('/matters')
    }
  }, [status, router])

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[var(--background)]">
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
              className="w-16 h-16 rounded-2xl bg-[var(--color-lila-600)] flex items-center justify-center shadow-lg shadow-[var(--color-lila-500)]/20"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-[var(--foreground)] mb-2 tracking-tight">MESA Law</h1>
            <p className="text-[var(--color-anthracite-400)] text-sm">Güvenli Hukuk Asistanı ve Zeka Platformu</p>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => signIn('keycloak', { callbackUrl: '/matters' })}
              className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] text-white border border-[var(--border-surface)] rounded-xl font-medium transition-all hover:scale-[1.02] active:scale-95 shadow-sm"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="https://upload.wikimedia.org/wikipedia/commons/2/29/Keycloak_Logo.png" alt="Keycloak" className="h-5 object-contain opacity-90" />
              Sign in with Keycloak
            </button>

          </div>
        </div>
      </motion.div>
    </div>
  )
}
