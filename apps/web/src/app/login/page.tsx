'use client'

import { signIn } from 'next-auth/react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Shield, ArrowRight } from 'lucide-react'

export default function LoginPage() {
  const [tenantId, setTenantId] = useState('')
  const router = useRouter()

  const handleTestSignIn = (e: React.FormEvent) => {
    e.preventDefault()
    if (tenantId.trim()) {
      localStorage.setItem('mesa_tenant_id', tenantId)
      document.cookie = `x-tenant-id=${tenantId}; path=/`
      router.push('/matters')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#030303]">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse" style={{ animationDelay: '2s' }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md p-8 relative z-10"
      >
        <div className="glass-card rounded-2xl p-10 border border-white/10 shadow-2xl backdrop-blur-2xl bg-black/40">
          <div className="flex justify-center mb-8">
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
          </div>

          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">MESA Law</h1>
            <p className="text-zinc-400 text-sm">Secure Legal Intelligence Platform</p>
          </div>

          <div className="space-y-6">
            <button
              onClick={() => signIn('keycloak', { callbackUrl: '/matters' })}
              className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-white hover:bg-zinc-100 text-black rounded-xl font-semibold transition-all hover:scale-[1.02] active:scale-95"
            >
              <img src="https://upload.wikimedia.org/wikipedia/commons/2/29/Keycloak_Logo.png" alt="Keycloak" className="h-5 object-contain" />
              Sign in with Keycloak
            </button>

            {process.env.NEXT_PUBLIC_MESA_LAW_DEMO_MODE === 'true' && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="pt-6 border-t border-white/10"
              >
                <p className="text-xs font-medium text-zinc-500 mb-3 uppercase tracking-wider">Developer Access</p>
                <form onSubmit={handleTestSignIn} className="flex gap-2">
                  <input 
                    type="text" 
                    placeholder="Tenant ID (e.g. e2e-123)"
                    value={tenantId}
                    onChange={(e) => setTenantId(e.target.value)}
                    className="flex-1 bg-black/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-zinc-600"
                  />
                  <button
                    type="submit"
                    className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 rounded-xl flex items-center justify-center transition-all hover:scale-[1.05]"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </form>
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
