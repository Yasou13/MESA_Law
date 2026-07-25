'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function LoginPage() {
  const router = useRouter()
  const [tenant, setTenant] = useState('mesa-law-tenant-1')

  const handleLogin = () => {
    localStorage.setItem('tenant_id', tenant)
    router.push('/matters')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-white">
      <div className="w-full max-w-md p-8 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl">
        <h1 className="text-3xl font-bold mb-6 text-center tracking-tight">MESA Law</h1>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-zinc-400">Firm / Tenant ID</label>
            <input 
              type="text"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-blue-500 text-white transition-colors"
            />
          </div>
          <button 
            onClick={handleLogin}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
          >
            Sign In (Mock SSO)
          </button>
        </div>
      </div>
    </div>
  )
}
