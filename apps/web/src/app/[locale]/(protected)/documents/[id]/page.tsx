'use client'

import { useParams } from 'next/navigation'
import { useGetDocument, useDownloadDocument } from '@/api/endpoints/default/default'
import { FileText, Download, AlertTriangle, ArrowLeft, Clock, Send, Bot, User } from 'lucide-react'
import Link from 'next/link'
import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function DocumentViewerPage() {
  const params = useParams()
  const documentId = params.id as string

  const { data: docRes, isLoading: loadingDoc } = useGetDocument(documentId)
  const { data: dlRes, isLoading: loadingDl, isError: dlError } = useDownloadDocument(documentId, {
    query: {
      enabled: (docRes?.data as any)?.status === 'clean'
    }
  })

  const doc = docRes?.data as any
  const presignedUrl = (dlRes?.data as any)?.presigned_url

  // Chat UI Stub state
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', content: string }[]>([
    { role: 'ai', content: 'Hello! I have analyzed this document. What would you like to know about it?' }
  ])
  const [chatInput, setChatInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return
    
    setMessages(prev => [...prev, { role: 'user', content: chatInput }])
    setChatInput('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'ai', content: 'This is a simulated response. The document chat API is not connected yet, but the interface is ready.' }])
      setIsTyping(false)
    }, 1500)
  }

  if (loadingDoc) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Document not found</h2>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col md:flex-row bg-[var(--background)] overflow-hidden">
      {/* Left Panel: Document Viewer */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-[var(--border-surface)]">
        <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-wrap items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <Link href="/documents" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg transition-colors shrink-0">
              <ArrowLeft className="w-5 h-5 text-[var(--color-anthracite-400)]" />
            </Link>
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-[var(--color-lila-500)] shrink-0" />
                <h1 className="text-lg font-bold tracking-tight truncate text-[var(--foreground)]">{doc.title}</h1>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3 shrink-0">
            <span className={`text-xs font-medium px-2 py-1 rounded-md border ${
              doc.status === 'clean' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
              doc.status === 'processing' ? 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20' : 
              'bg-red-500/10 text-red-400 border-red-500/20'
            }`}>
              {doc.status?.toUpperCase()}
            </span>
            {presignedUrl && (
              <a 
                href={presignedUrl} 
                download
                className="flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-surface-hover)] hover:bg-[var(--bg-surface)] text-[var(--foreground)] border border-[var(--border-surface)] rounded-lg transition-colors text-xs font-medium"
              >
                <Download className="w-4 h-4" />
                Original
              </a>
            )}
          </div>
        </div>

        <div className="flex-1 bg-zinc-950 relative overflow-hidden">
          {doc?.status === 'clean' && presignedUrl ? (
            <iframe 
              src={`${presignedUrl}#toolbar=0`} 
              className="w-full h-full border-none bg-white rounded-none"
              title={doc.title}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-surface)] p-6">
              <div className={`text-center max-w-md p-8 rounded-2xl border shadow-sm ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'bg-red-500/5 border-red-500/20' : 'bg-[var(--bg-surface-hover)] border-[var(--border-surface)]'}`}>
                {doc?.status === 'clean' && loadingDl && (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)] mx-auto mb-4"></div>
                )}
                {(doc?.status === 'quarantined' || doc?.status === 'infected') && (
                  <div className="bg-red-500/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                  </div>
                )}
                {(doc?.status === 'processing' || doc?.status === 'scanning') && (
                  <Clock className="w-12 h-12 text-[var(--color-anthracite-400)] mx-auto mb-4 animate-pulse" />
                )}
                <h3 className={`text-xl font-bold mb-2 ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'text-red-500' : 'text-[var(--foreground)]'}`}>
                  {doc?.status === 'clean' && dlError ? 'Failed to load preview' : 
                   (doc?.status === 'quarantined' || doc?.status === 'infected') ? 'SECURITY ALERT' : 'Preview Unavailable'}
                </h3>
                <p className={`text-sm ${doc?.status === 'quarantined' || doc?.status === 'infected' ? 'text-red-400' : 'text-[var(--color-anthracite-400)]'}`}>
                  {doc?.status === 'clean' 
                    ? 'We could not generate a secure preview URL for this document.' 
                    : (doc?.status === 'quarantined' || doc?.status === 'infected') 
                      ? 'This document has failed security checks (virus/malware detected). Access is strictly prohibited.'
                      : 'This document is currently being processed. Preview will be available once processing completes.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Chat Interface */}
      <div className="w-full md:w-[400px] flex flex-col bg-[var(--bg-surface)] shrink-0 border-t md:border-t-0">
        <div className="p-4 border-b border-[var(--border-surface)]">
          <h2 className="font-semibold text-[var(--foreground)] flex items-center gap-2">
            <Bot className="w-4 h-4 text-[var(--color-lila-500)]" />
            Chat with Document
          </h2>
          <p className="text-xs text-[var(--color-anthracite-400)] mt-1">Ask questions about this specific document.</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'ai' && (
                <div className="w-8 h-8 rounded-full bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-[var(--color-lila-500)]" />
                </div>
              )}
              <div className={`p-3 rounded-xl max-w-[85%] text-sm ${
                msg.role === 'user' 
                  ? 'bg-[var(--color-lila-500)] text-white' 
                  : 'bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] text-[var(--foreground)]'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-[var(--color-anthracite-700)] flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          {isTyping && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-[var(--color-lila-500)]" />
              </div>
              <div className="p-3 rounded-xl bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] text-[var(--color-anthracite-400)] text-sm flex gap-1 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[var(--border-surface)] bg-[var(--bg-surface)]">
          <form onSubmit={handleSendChat} className="relative flex items-center">
            <Input 
              type="text"
              placeholder="Ask a question..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              className="pr-12 w-full bg-[var(--background)]"
              disabled={isTyping}
            />
            <Button 
              type="submit" 
              size="icon-sm"
              variant="ghost" 
              className="absolute right-1 text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)]"
              disabled={!chatInput.trim() || isTyping}
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
