'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import Link from 'next/link'
import { useState } from 'react'
import { Plus, FolderOpen, Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'

type Matter = {
  id: string
  title: string
  status: string
}

export default function MattersPage() {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')

  const { data: matters, isLoading } = useQuery<Matter[]>({
    queryKey: ['matters'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/matters')
      return res.data
    }
  })

  const createMatter = useMutation({
    mutationFn: async (title: string) => {
      const res = await axios.post('/api/v1/matters', { title })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matters'] })
      setNewTitle('')
      toast.success('Matter created successfully')
    },
    onError: () => {
      toast.error('Failed to create matter')
    }
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    createMatter.mutate(newTitle)
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Matters</h1>
        
        <form onSubmit={handleCreate} className="flex gap-3">
          <input 
            type="text" 
            placeholder="New matter title..." 
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button 
            type="submit" 
            disabled={createMatter.isPending || !newTitle.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg font-medium transition-colors text-sm"
          >
            {createMatter.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Create
          </button>
        </form>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {matters?.map((matter) => (
            <Link 
              key={matter.id} 
              href={`/matters/${matter.id}`}
              className="block p-6 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-all hover:-translate-y-1 group"
            >
              <div className="flex items-start justify-between">
                <FolderOpen className="w-8 h-8 text-blue-500 mb-4" />
                <span className="px-2.5 py-1 text-xs font-medium bg-zinc-800 text-zinc-300 rounded-full">
                  {matter.status}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-zinc-100 group-hover:text-blue-400 transition-colors">
                {matter.title}
              </h3>
              <p className="text-sm text-zinc-500 mt-2 font-mono">
                {matter.id.substring(0, 8)}...
              </p>
            </Link>
          ))}
          {matters?.length === 0 && (
            <div className="col-span-full text-center py-12 text-zinc-500">
              No matters found. Create one to get started.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
