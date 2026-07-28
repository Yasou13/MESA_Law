'use client'

import { useState } from 'react'
import { ZoomIn, ZoomOut, Download, Send, Loader2, Bot, User, MessageSquare, AlertCircle } from 'lucide-react'
import { useAskQuestion } from '@/api/endpoints/qa/qa'
import { toast } from 'react-hot-toast'

interface DocumentViewerProps {
  documentId: string
  matterId: string
  url: string
  title: string
  onClose: () => void
}

export function DocumentViewer({ documentId, matterId, url, title, onClose }: DocumentViewerProps) {
  const [zoom, setZoom] = useState(100)
  
  // Chat state
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState<{role: 'user' | 'ai', content: string, citations?: any[], review_warning?: boolean, source_coverage?: string}[]>([
    { role: 'ai', content: 'Ask me anything about this document.' }
  ])
  const askMutation = useAskQuestion()

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const newQuery = chatInput
    setMessages(prev => [...prev, { role: 'user', content: newQuery }])
    setChatInput('')

    try {
      const response = await askMutation.mutateAsync({ 
        data: { matter_id: matterId, document_id: documentId, question: newQuery } 
      })
      const data = response.data as any
      const formattedCitations = data.citations?.map((c: any) => `Page ${c.page_number}`) || []
      
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: data.answer || 'No relevant answer found in this document.',
        citations: formattedCitations,
        review_warning: data.review_warning,
        source_coverage: data.source_coverage
      }])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to retrieve answer")
      setMessages(prev => [...prev, { role: 'ai', content: "An error occurred while answering." }])
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[var(--background)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] shrink-0">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-medium text-[var(--foreground)]">{title}</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-[var(--bg-surface-hover)] rounded-lg p-1 border border-[var(--border-surface)]">
            <button onClick={() => setZoom(z => Math.max(50, z - 10))} className="p-1.5 hover:bg-[var(--color-anthracite-700)] rounded text-[var(--color-anthracite-300)] hover:text-white transition-colors">
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs font-medium px-2 text-[var(--color-anthracite-200)]">{zoom}%</span>
            <button onClick={() => setZoom(z => Math.min(200, z + 10))} className="p-1.5 hover:bg-[var(--color-anthracite-700)] rounded text-[var(--color-anthracite-300)] hover:text-white transition-colors">
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
          <a href={url} target="_blank" rel="noopener noreferrer" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg text-[var(--color-anthracite-300)] hover:text-white transition-colors border border-transparent hover:border-[var(--border-surface)]">
            <Download className="w-5 h-5" />
          </a>
          <button onClick={onClose} className="px-4 py-2 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] text-white rounded-lg text-sm font-medium transition-colors">
            Close Viewer
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        
        {/* PDF Viewer Area */}
        <div className="flex-1 flex bg-[var(--color-anthracite-900)] p-4 md:p-8 overflow-hidden">
          <div className="flex-1 bg-white rounded-xl shadow-2xl overflow-hidden flex items-center justify-center relative">
             <iframe 
              src={`${url}#zoom=${zoom}`} 
              className="w-full h-full border-0"
              title={title}
            />
          </div>
        </div>
        
        {/* Document Chat Panel */}
        <div className="w-[400px] border-l border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-col shrink-0">
          <div className="p-4 border-b border-[var(--border-surface)] flex items-center gap-2 bg-[var(--bg-surface-hover)] shrink-0">
            <MessageSquare className="w-5 h-5 text-[var(--color-lila-500)]" />
            <h3 className="font-semibold text-sm text-[var(--foreground)]">Document AI</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[90%] rounded-2xl p-3 text-sm shadow-sm flex flex-col gap-2 ${msg.role === 'user' ? 'bg-[var(--color-anthracite-800)] text-white border border-[var(--color-anthracite-700)] rounded-tr-sm' : msg.review_warning ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 rounded-tl-sm' : 'bg-[var(--bg-surface-hover)] text-[var(--foreground)] border border-[var(--border-surface)] rounded-tl-sm'}`}>
                  {msg.review_warning && (
                    <div className="flex items-center gap-1.5 mb-0.5 font-semibold text-xs uppercase tracking-wider">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Verification Warning
                    </div>
                  )}
                  {msg.source_coverage === 'INVALID' && (
                    <div className="text-red-500 font-medium mb-0.5 text-xs">
                      Response blocked due to unverified citations.
                    </div>
                  )}
                  <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-[var(--border-surface)]/20">
                      <ul className="text-[10px] space-y-1">
                        {msg.citations.map((cit, cIdx) => (
                          <li key={cIdx} className="text-[var(--color-lila-400)] flex items-start gap-1">
                            <span className="mt-0.5">•</span>
                            <span>{cit}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {askMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-2xl rounded-tl-sm p-3 flex gap-2 items-center">
                  <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-75"></div>
                  <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-150"></div>
                </div>
              </div>
            )}
          </div>
          
          <form onSubmit={handleSendChat} className="p-3 bg-[var(--bg-surface)] border-t border-[var(--border-surface)] flex gap-2 shrink-0">
            <input 
              type="text" 
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Ask about this document..." 
              className="flex-1 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg px-3 py-2 text-sm text-[var(--foreground)] focus:outline-none focus:border-[var(--color-lila-500)] transition-colors placeholder:text-[var(--color-anthracite-500)]"
              disabled={askMutation.isPending}
            />
            <button 
              type="submit" 
              disabled={askMutation.isPending || !chatInput.trim()}
              className="bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] disabled:opacity-50 disabled:hover:bg-[var(--color-lila-600)] text-white px-3 py-2 rounded-lg text-sm font-medium transition-all shadow-sm flex items-center justify-center min-w-[2.5rem]"
            >
              {askMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
