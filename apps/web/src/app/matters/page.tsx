'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import Link from 'next/link'
import { useState } from 'react'
import { Plus, FolderOpen, Loader2, Search, ArrowRight, Activity, Clock } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'

type Matter = {
  id: string
  title: string
  status: string
}

export default function MattersPage() {
  const queryClient = useQueryClient()
  const [newTitle, setNewTitle] = useState('')
  const [search, setSearch] = useState('')

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
      toast.success('Matter workspace initialized')
    },
    onError: () => {
      toast.error('Failed to create workspace')
    }
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    createMatter.mutate(newTitle)
  }

  const filteredMatters = matters?.filter(m => m.title.toLowerCase().includes(search.toLowerCase())) || []

  return (
    <div className="max-w-7xl mx-auto p-8 lg:p-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-white mb-2">Matter Workspaces</h1>
          <p className="text-zinc-400">Manage and analyze your legal cases with AI intelligence.</p>
        </div>
        
        <form onSubmit={handleCreate} className="flex gap-3 w-full md:w-auto relative group">
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
          <input 
            type="text" 
            placeholder="New matter name..." 
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="px-5 py-3 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:border-blue-500/50 focus:bg-white/10 text-sm text-white w-full md:w-64 transition-all relative z-10 backdrop-blur-md placeholder:text-zinc-500"
          />
          <button 
            type="submit" 
            disabled={createMatter.isPending || !newTitle.trim()}
            className="flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-xl font-medium transition-all text-sm relative z-10 shadow-lg shadow-blue-500/20 disabled:shadow-none hover:scale-105 active:scale-95"
          >
            {createMatter.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-5 h-5" />}
            <span className="hidden sm:inline">Initialize</span>
          </button>
        </form>
      </div>

      <div className="mb-8 relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
        <input 
          type="text" 
          placeholder="Search matters by name or ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-4 glass-card rounded-2xl text-white placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50 transition-colors"
        />
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
          <p className="text-zinc-500 animate-pulse">Loading workspaces...</p>
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
        >
          {filteredMatters.map((matter, i) => (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              key={matter.id}
            >
              <Link 
                href={`/matters/${matter.id}`}
                className="block p-6 glass-card rounded-2xl hover:border-blue-500/30 transition-all duration-300 group relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                
                <div className="flex items-start justify-between relative z-10">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <FolderOpen className="w-6 h-6 text-blue-400" />
                  </div>
                  <span className={clsx(
                    "px-3 py-1 text-xs font-medium rounded-full border",
                    matter.status === 'ACTIVE' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-zinc-800/50 text-zinc-400 border-zinc-700/50"
                  )}>
                    {matter.status}
                  </span>
                </div>
                
                <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors relative z-10 mb-2 truncate">
                  {matter.title}
                </h3>
                
                <div className="flex items-center gap-4 mt-6 text-sm text-zinc-500 relative z-10">
                  <div className="flex items-center gap-1.5">
                    <Activity className="w-4 h-4" />
                    <span>0 Docs</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    <span className="font-mono">{matter.id.substring(0, 6)}</span>
                  </div>
                </div>

                <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all text-blue-400">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </Link>
            </motion.div>
          ))}
          {filteredMatters.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center py-24 glass-card rounded-3xl border-dashed border-2 border-white/10">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                <FolderOpen className="w-8 h-8 text-zinc-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">No workspaces found</h3>
              <p className="text-zinc-500 text-center max-w-sm">
                Get started by creating your first legal matter workspace using the form above.
              </p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}

