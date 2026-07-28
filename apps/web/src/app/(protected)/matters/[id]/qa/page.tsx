'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { useMatterQA } from '@/api/endpoints/default/default'
import { Send, Bot, User, AlertTriangle, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { useSystemDependenciesApiV1SystemDependenciesGet } from '@/api/endpoints/system/system'

export default function MatterQAPage() {
  const params = useParams()
  const matterId = params.id as string
  
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'ai', content: string, citations?: any[] }>>([])
  
  const { data: depsRes } = useSystemDependenciesApiV1SystemDependenciesGet()
  const isMockAdapter = (depsRes?.data as any)?.intelligence_adapter === 'mock'

  const { mutate: askQuestion, isPending } = useMatterQA()

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isPending) return

    const userMsg = query.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setQuery('')
    
    askQuestion({ matterId, data: { question: userMsg } as any }, {
      onSuccess: (res: any) => {
        setMessages(prev => [
          ...prev, 
          { 
            role: 'ai', 
            content: res.data.answer, 
            citations: res.data.citations 
          }
        ])
      },
      onError: () => {
        setMessages(prev => [
          ...prev, 
          { 
            role: 'ai', 
            content: 'Sorry, I encountered an error while processing your request.' 
          }
        ])
      }
    })
  }

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto">
      <div className="flex items-center gap-4 py-4 shrink-0">
        <Link href={`/matters/${matterId}`} className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5 text-zinc-400" />
        </Link>
        <div>
          <h1 className="text-xl font-bold tracking-tight">Matter Intelligence</h1>
          <p className="text-sm text-zinc-400">Ask questions about documents in this matter.</p>
        </div>
      </div>

      <div className="flex-1 glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden flex flex-col mt-4">
        {isMockAdapter && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-amber-500 font-medium">Running in MOCK intelligence mode. Results are simulated.</span>
          </div>
        )}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-zinc-400">
              <Bot className="w-12 h-12 mb-4 opacity-50" />
              <p>Ask anything about this matter&apos;s documents.</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-[var(--color-lila-500)] text-white' : 'bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] text-[var(--color-lila-400)]'}`}>
                  {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                <div className={`max-w-[80%] rounded-xl p-4 ${msg.role === 'user' ? 'bg-[var(--color-lila-500)]/10 text-[var(--foreground)]' : 'bg-[var(--bg-surface)] border border-[var(--border-surface)]'}`}>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                  
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-[var(--border-surface)] space-y-2">
                      <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Citations</h4>
                      {msg.citations.map((cit, idx) => (
                        <div key={idx} className="bg-[var(--bg-surface-hover)] rounded-md p-2 text-xs">
                          <span className="font-medium text-[var(--color-lila-400)]">Doc {cit.document_id} (Page {cit.page_number}):</span>
                          <span className="text-zinc-400 ml-1">"{cit.text_snippet}..."</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isPending && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-lg bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] text-[var(--color-lila-400)] flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-xl p-4 flex items-center gap-2 text-sm text-zinc-400">
                <div className="w-2 h-2 bg-[var(--color-lila-400)] rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-[var(--color-lila-400)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-[var(--color-lila-400)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 bg-[var(--bg-surface)] border-t border-[var(--border-surface)]">
          <form onSubmit={handleAsk} className="relative flex items-center">
            <input 
              type="text" 
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Ask AI about this matter..."
              className="w-full bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-xl py-4 pl-4 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)] text-[var(--foreground)]"
            />
            <button 
              type="submit"
              disabled={!query.trim() || isPending}
              className="absolute right-2 p-2 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
