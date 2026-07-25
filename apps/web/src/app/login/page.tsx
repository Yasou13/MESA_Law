'use client'
import { signIn } from 'next-auth/react'
import { useState } from 'react'

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [tenantId, setTenantId] = useState('')

  const handleSignIn = async () => {
    setLoading(true)
    try {
      await signIn('keycloak', { callbackUrl: '/matters' })
    } catch (error) {
      console.error('Sign in error:', error)
      setLoading(false)
    }
  }

  const handleTestSignIn = () => {
    if (tenantId.trim()) {
      localStorage.setItem('tenant_id', tenantId.trim())
      localStorage.setItem('user_id', 'test-user-id')
      window.location.href = '/matters'
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <div className="w-full max-w-md p-8 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl">
        <h1 className="text-3xl font-bold mb-6 text-center tracking-tight">MESA Law</h1>
        <div className="space-y-4">
          <p className="text-gray-400 mt-2">MESA Law platformuna erişmek için lütfen giriş yapın. Eğer hesabınız yoksa, sistem yöneticinizden davet isteyin.</p>
          <button 
            onClick={handleSignIn}
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Redirecting to Keycloak...</span>
              </>
            ) : (
              'Sign In with Keycloak'
            )}
          </button>
          
          <div className="pt-4 border-t border-zinc-800 mt-4">
            <p className="text-xs text-zinc-500 mb-2">Developer / Test Login:</p>
            <div className="flex gap-2">
              <input 
                type="text" 
                placeholder="Enter Tenant ID (e.g. e2e-tenant-123)"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleTestSignIn}
                className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
