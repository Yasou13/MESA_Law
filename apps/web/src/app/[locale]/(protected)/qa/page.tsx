'use client'

import { useState } from 'react'
import { MessageSquare, Plus, Send, Bot, User, Globe, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function GlobalQAPage() {
  const [activeSession, setActiveSession] = useState<string>('new')
  const [chatInput, setChatInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([
    { role: 'ai', content: 'Hello! I am the global MESA AI assistant. I can search across all your firm\'s matters and documents. What would you like to know?' }
  ])
  
  const chatHistory = [
    { id: '1', title: 'Compare Liability Clauses across matters', date: '2 hours ago' },
    { id: '2', title: 'Firm-wide deadlines this week', date: 'Yesterday' },
    { id: '3', title: 'Search for similar IP disputes', date: 'Last week' },
  ]

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return
    
    setMessages(prev => [...prev, { role: 'user', content: chatInput }])
    setChatInput('')
    setIsTyping(true)

    // Simulate AI response for Global QA
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'ai', content: 'This is a simulated global search response. The global QA endpoint is not connected yet, but the interface is ready.' }])
      setIsTyping(false)
    }, 1500)
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden">
      {/* Left Panel: Chat History */}
      <div className="w-80 border-r border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-col shrink-0">
        <div className="p-4 border-b border-[var(--border-surface)]">
          <Button 
            className="w-full gap-2 justify-start bg-[var(--color-lila-500)] text-white hover:bg-[var(--color-lila-600)]"
            onClick={() => {
              setActiveSession('new')
              setMessages([{ role: 'ai', content: 'Hello! I am the global MESA AI assistant. I can search across all your firm\'s matters and documents. What would you like to know?' }])
            }}
          >
            <Plus className="w-4 h-4" /> New Global Search
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="px-3 py-2 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">
            Recent Searches
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

      {/* Main Content: Global QAShell UI */}
      <div className="flex-1 flex flex-col min-w-0 bg-[var(--bg-surface-hover)] p-6 md:p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto w-full space-y-6 flex flex-col h-full">
          <div className="shrink-0">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Global AI Search</h1>
            <p className="text-[var(--color-anthracite-500)] mt-1">Search intelligently across all matters, evidence, and claims in your firm.</p>
          </div>
          
          <div className="flex-1 flex flex-col border border-[var(--border-surface)] rounded-xl overflow-hidden bg-[var(--bg-surface)] shadow-sm min-h-0">
            <div className="bg-[var(--bg-surface-hover)] p-4 border-b border-[var(--border-surface)] flex justify-between items-center shrink-0">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-[var(--color-lila-500)]" />
                <h2 className="text-sm font-semibold text-[var(--foreground)]">Firm-wide Assistant</h2>
              </div>
              <span className="text-xs bg-[var(--color-lila-500)]/10 text-[var(--color-lila-400)] px-2.5 py-1 rounded-full border border-[var(--color-lila-500)]/20 font-medium">MESA Core Sync</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center shrink-0 mt-1">
                      <Globe className="w-4 h-4 text-[var(--color-lila-500)]" />
                    </div>
                  )}
                  <div className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-[var(--color-anthracite-800)] text-white border border-[var(--color-anthracite-700)] rounded-tr-sm' 
                      : 'bg-[var(--bg-surface-hover)] text-[var(--foreground)] border border-[var(--border-surface)] rounded-tl-sm'
                  }`}>
                    <p className="leading-relaxed">{msg.content}</p>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-[var(--color-anthracite-800)] flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              ))}
              
              {isTyping && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center shrink-0 mt-1">
                    <Globe className="w-4 h-4 text-[var(--color-lila-500)]" />
                  </div>
                  <div className="bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-2xl rounded-tl-sm p-4 flex gap-2 items-center">
                    <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-75"></div>
                    <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-150"></div>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSendChat} className="p-4 bg-[var(--bg-surface)] border-t border-[var(--border-surface)] flex gap-2 shrink-0">
              <Input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Search across all matters..." 
                className="flex-1 bg-[var(--background)]"
                disabled={isTyping}
              />
              <Button 
                type="submit" 
                disabled={isTyping || !chatInput.trim()}
                className="bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] text-white px-6 shadow-sm"
              >
                {isTyping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                {isTyping ? '' : 'Search'}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
