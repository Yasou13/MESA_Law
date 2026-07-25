'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useListMatters, useCreateMatter } from '@/api/endpoints/default/default'
import Link from 'next/link'

export default function MattersPage() {
  const router = useRouter()
  const { data: mattersResponse, isLoading, refetch } = useListMatters()
  const matters = mattersResponse?.data || []
  const createMatterMutation = useCreateMatter()
  const [newTitle, setNewTitle] = useState('')

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    await createMatterMutation.mutateAsync({ data: { title: newTitle } })
    setNewTitle('')
    refetch()
  }

  if (isLoading) return <div className="p-8 text-white">Loading matters...</div>

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Matters</h1>
          <button onClick={() => {
            localStorage.removeItem('tenant_id');
            router.push('/login');
          }} className="text-sm text-zinc-400 hover:text-white transition-colors">Sign out</button>
        </header>

        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl space-y-4">
          <h2 className="text-lg font-medium">Create New Matter</h2>
          <div className="flex gap-4">
            <input 
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Smith vs. Johnson"
              className="flex-1 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
            />
            <button 
              onClick={handleCreate}
              disabled={createMatterMutation.isPending}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </div>

        <div className="grid gap-4">
          {Array.isArray(matters) && matters.map((matter) => (
            <Link 
              key={matter.id}
              href={`/matters/${matter.id}`}
              className="block bg-zinc-900 border border-zinc-800 hover:border-zinc-700 p-6 rounded-xl transition-all hover:shadow-lg hover:shadow-blue-900/10"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-medium">{matter.title}</h3>
                  <p className="text-sm text-zinc-500 mt-1">Status: {matter.status}</p>
                </div>
                <span className="text-blue-500 group-hover:translate-x-1 transition-transform">→</span>
              </div>
            </Link>
          ))}
          {Array.isArray(matters) && matters.length === 0 && (
            <div className="text-center text-zinc-500 py-12">No matters found. Create one above.</div>
          )}
        </div>
      </div>
    </div>
  )
}
