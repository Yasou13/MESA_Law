'use client'
import { signIn } from 'next-auth/react'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <div className="w-full max-w-md p-8 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl">
        <h1 className="text-3xl font-bold mb-6 text-center tracking-tight">MESA Law</h1>
        <div className="space-y-4">
          <p className="text-gray-400 mt-2">MESA Law platformuna erişmek için lütfen giriş yapın. Eğer hesabınız yoksa, sistem yöneticinizden davet isteyin.</p>
          <button 
            onClick={() => signIn('keycloak', { callbackUrl: '/matters' })}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
          >
            Sign In with Keycloak
          </button>
        </div>
      </div>
    </div>
  )
}
