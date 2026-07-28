'use client'

import { use, useState } from 'react'
import { ArrowLeft, MessageSquare, Plus, Clock } from 'lucide-react'
import Link from 'next/link'
import { QAShell } from '@/features/qa/components/QAShell'
import { Button } from '@/components/ui/button'

export default function MatterQAPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  // UI Stub for chat history
  const [activeSession, setActiveSession] = useState<string>('new')
  
  const chatHistory = [
    { id: '1', title: 'Analysis of Liability', date: '2 hours ago' },
    { id: '2', title: 'Contract Breach Clauses', date: 'Yesterday' },
    { id: '3', title: 'Key Dates in Timeline', date: 'Last week' },
  ]

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden">
      {/* Left Panel: Chat History */}
      <div className="w-80 border-r border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-col shrink-0">
        <div className="p-4 border-b border-[var(--border-surface)]">
          <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors mb-4">
            <ArrowLeft className="w-4 h-4" /> Back to Matter
          </Link>
          <Button 
            className="w-full gap-2 justify-start bg-[var(--color-lila-500)] text-white hover:bg-[var(--color-lila-600)]"
            onClick={() => setActiveSession('new')}
          >
            <Plus className="w-4 h-4" /> New Chat Session
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="px-3 py-2 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">
            Recent Sessions
          </div>
          {chatHistory.map(session => (
            <button
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center justify-between group transition-colors ${
                activeSession === session.id 
                  ? 'bg-[var(--bg-surface-hover)] text-[var(--color-lila-500)]' 
                  : 'text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]'
              }`}
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <MessageSquare className={`w-4 h-4 shrink-0 ${activeSession === session.id ? 'text-[var(--color-lila-500)]' : 'text-[var(--color-anthracite-400)]'}`} />
                <span className="text-sm font-medium truncate">{session.title}</span>
              </div>
              <span className="text-[10px] text-[var(--color-anthracite-500)] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                {session.date}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content: QAShell */}
      <div className="flex-1 flex flex-col min-w-0 bg-[var(--bg-surface-hover)] p-6 md:p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto w-full space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Matter Q&A</h1>
            <p className="text-[var(--color-anthracite-500)] mt-1">Ask questions about this matter based on the evidence and timeline.</p>
          </div>
          
          <div className="h-[650px] shadow-sm rounded-xl overflow-hidden border border-[var(--border-surface)]">
            {/* We force a re-render of QAShell when switching sessions (stub behavior) */}
            <QAShell key={activeSession} matterId={matterId} />
          </div>
        </div>
      </div>
    </div>
  )
}
