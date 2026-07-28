'use client'

import { useState, useEffect } from 'react'
import { Command, Server, Shield, Users, Database, Zap, Activity } from 'lucide-react'
import { useSystemDependenciesApiV1SystemDependenciesGet } from '@/api/endpoints/system/system'

export function OperationsMenu() {
  const [isOpen, setIsOpen] = useState(false)
  const { data: depsRes } = useSystemDependenciesApiV1SystemDependenciesGet(
    { query: { enabled: isOpen } }
  )
  const deps = depsRes?.data || {}
  const allOk = Object.values(deps).every(v => v === 'ok' || v === 'degraded')

  // CMD+Shift+K shortcut (CMD+K is used by CommandMenu)
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey) && e.shiftKey) {
        e.preventDefault()
        setIsOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-[var(--background)]/80 backdrop-blur-sm" onClick={() => setIsOpen(false)}>
      <div 
        className="w-full max-w-xl bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center px-4 border-b border-[var(--border-surface)]">
          <Command className="w-5 h-5 text-[var(--color-anthracite-400)] mr-3" />
          <input 
            type="text" 
            placeholder="Search operations, commands, or quick actions..."
            className="flex-1 bg-transparent border-0 py-4 text-sm text-[var(--foreground)] focus:ring-0 focus:outline-none placeholder:text-[var(--color-anthracite-500)]"
            autoFocus
          />
          <div className="text-[var(--color-anthracite-400)] text-xs font-mono bg-[var(--bg-surface-hover)] px-2 py-1 rounded border border-[var(--border-surface)]">ESC</div>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-2">
          <div className="px-2 py-1.5 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">System Operations</div>
          
          <button className="w-full flex items-center px-3 py-2.5 rounded-lg text-sm text-[var(--foreground)] hover:bg-[var(--color-lila-500)] hover:text-white group transition-colors">
            <Server className="w-4 h-4 text-[var(--color-anthracite-400)] group-hover:text-white mr-3" />
            <div className="flex-1 text-left">View System Logs</div>
          </button>
          <button className="w-full flex items-center px-3 py-2.5 rounded-lg text-sm text-[var(--foreground)] hover:bg-[var(--color-lila-500)] hover:text-white group transition-colors">
            <Activity className="w-4 h-4 text-[var(--color-anthracite-400)] group-hover:text-white mr-3" />
            <div className="flex-1 text-left">Check Background Workers Status</div>
            <span className={`text-xs px-2 py-0.5 rounded-full ${allOk ? 'bg-emerald-500/20 text-emerald-500 group-hover:text-white group-hover:bg-white/20' : 'bg-red-500/20 text-red-500 group-hover:text-white group-hover:bg-white/20'}`}>
              {allOk ? 'Healthy' : 'Issues Detected'}
            </span>
          </button>

          <div className="px-2 py-1.5 mt-4 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">Administration</div>
          
          <button className="w-full flex items-center px-3 py-2.5 rounded-lg text-sm text-[var(--foreground)] hover:bg-[var(--color-lila-500)] hover:text-white group transition-colors">
            <Users className="w-4 h-4 text-[var(--color-anthracite-400)] group-hover:text-white mr-3" />
            <div className="flex-1 text-left">Manage Organization Members</div>
          </button>
        </div>
        
        <div className="bg-[var(--bg-surface-hover)] px-4 py-3 border-t border-[var(--border-surface)] text-xs text-[var(--color-anthracite-400)] flex justify-between">
          <span>Search for commands</span>
          <span className="flex items-center gap-1">Press <kbd className="font-mono bg-[var(--bg-surface)] px-1 py-0.5 rounded border border-[var(--border-surface)]">↑</kbd> <kbd className="font-mono bg-[var(--bg-surface)] px-1 py-0.5 rounded border border-[var(--border-surface)]">↓</kbd> to navigate</span>
        </div>
      </div>
    </div>
  )
}
