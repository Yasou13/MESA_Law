'use client'

import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useState } from 'react'
import { Plus, FolderOpen, Loader2, Search, ArrowRight, Activity, Clock } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'
import { useListMatters, useCreateMatter } from '@/api/endpoints/default/default'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const matterSchema = z.object({
  title: z.string().min(3, 'Matter name must be at least 3 characters'),
})

type MatterFormValues = z.infer<typeof matterSchema>

export default function MattersPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')

  const { data: mattersResponse, isLoading } = useListMatters()
  const matters = Array.isArray(mattersResponse?.data) ? mattersResponse.data : []

  const { register, handleSubmit, reset, formState: { errors } } = useForm<MatterFormValues>({
    resolver: zodResolver(matterSchema),
    defaultValues: { title: '' }
  })

  const createMatter = useCreateMatter({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['/api/v1/matters'] })
        reset()
        toast.success('Matter workspace initialized')
      },
      onError: () => {
        toast.error('Failed to create workspace')
      }
    }
  })

  const onSubmit = (data: MatterFormValues) => {
    createMatter.mutate({ data: { title: data.title } as any })
  }

  const filteredMatters = matters?.filter(m => m.title.toLowerCase().includes(search.toLowerCase())) || []

  return (
    <div className="max-w-7xl mx-auto p-8 lg:p-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-[var(--foreground)] mb-2">Matter Workspaces</h1>
          <p className="text-[var(--color-anthracite-400)]">Manage and analyze your legal cases with AI intelligence.</p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-1 w-full md:w-auto relative group">
          <div className="flex gap-3 relative">
            <input 
              type="text" 
              placeholder="New matter name..." 
              {...register('title')}
              className="px-5 py-3 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl focus:outline-none focus:border-[var(--color-lila-500)] text-sm text-[var(--foreground)] w-full md:w-64 transition-all relative z-10 placeholder:text-[var(--color-anthracite-400)]"
            />
            <button 
              type="submit" 
              disabled={createMatter.isPending}
              className="flex items-center justify-center gap-2 px-5 py-3 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] disabled:bg-[var(--bg-surface-hover)] disabled:text-[var(--color-anthracite-400)] text-white border border-[var(--border-surface)] rounded-xl font-medium transition-all text-sm relative z-10 shadow-sm disabled:shadow-none hover:scale-105 active:scale-95"
            >
              {createMatter.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-5 h-5" />}
              <span className="hidden sm:inline">Initialize</span>
            </button>
          </div>
          {errors.title && (
            <p className="text-sm text-[var(--color-semantic-error)] px-2">{errors.title.message}</p>
          )}
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

