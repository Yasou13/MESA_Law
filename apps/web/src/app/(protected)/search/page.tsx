'use client'

import { useState } from 'react'
import { Search, FileText, Folder } from 'lucide-react'
import { useListAllDocuments } from '@/api/endpoints/default/default'
import { useListMatters } from '@/api/endpoints/default/default'
import Link from 'next/link'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  
  const { data: docRes } = useListAllDocuments()
  const { data: matterRes } = useListMatters()

  const documents = docRes?.data || []
  const matters = matterRes?.data || []

  const searchResults = () => {
    if (!query) return []
    const q = query.toLowerCase()
    
    const docs = (documents as any[]).filter((d: any) => d.title?.toLowerCase().includes(q) || d.content_hash?.toLowerCase().includes(q)).map((d: any) => ({ ...d, type: 'document' }))
    const matts = (matters as any[]).filter((m: any) => m.name?.toLowerCase().includes(q) || m.description?.toLowerCase().includes(q)).map((m: any) => ({ ...m, type: 'matter' }))
    
    return [...docs, ...matts]
  }

  const results = searchResults()

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Global Search</h1>
        <p className="text-zinc-400">Search across matters, documents, and resources.</p>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search... (Try 'Matter' or 'Document')" 
          className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl py-4 pl-12 pr-4 text-[var(--foreground)] placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)]"
        />
      </div>

      {query && (
        <div className="glass-card rounded-xl overflow-hidden divide-y divide-[var(--border-surface)]">
          {results.length === 0 ? (
            <div className="p-8 text-center text-zinc-400">
              No results found for "{query}".
            </div>
          ) : (
            results.map((res: any) => (
              <Link 
                key={res.id} 
                href={res.type === 'matter' ? `/matters/${res.id}` : `/documents/${res.id}`}
                className="p-4 hover:bg-[var(--bg-surface-hover)] transition-colors flex items-center gap-4 block"
              >
                <div className="w-10 h-10 rounded-lg bg-[var(--bg-surface)] flex items-center justify-center border border-[var(--border-surface)]">
                  {res.type === 'matter' ? <Folder className="w-5 h-5 text-blue-400" /> : <FileText className="w-5 h-5 text-purple-400" />}
                </div>
                <div>
                  <h4 className="text-sm font-semibold">{res.name || res.title}</h4>
                  <p className="text-xs text-zinc-500 capitalize">{res.type} • {res.status || 'Active'}</p>
                </div>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}
