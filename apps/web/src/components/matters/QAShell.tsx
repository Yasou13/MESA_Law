import React, { useState } from 'react';
import { useMatterQA } from '@/api/endpoints/default/default';
import { Send, Loader2, BookOpen, AlertCircle } from 'lucide-react';

export function QAShell({ matterId = "1" }: { matterId?: string }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{role: 'user' | 'ai', content: string, citations?: string[]}[]>([]);
  
  const qaMutation = useMatterQA();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const newQuery = query;
    setMessages(prev => [...prev, { role: 'user', content: newQuery }]);
    setQuery('');

    qaMutation.mutate(
      { matterId, data: { question: newQuery } },
      {
        onSuccess: (res: any) => {
          const data = res.data;
          const formattedCitations = data.citations?.map((c: any) => `${c.doc_title} (Page ${c.page_number})`) || [];
          
          setMessages(prev => [...prev, { 
            role: 'ai', 
            content: data.answer || 'No relevant answer found.', 
            citations: formattedCitations 
          }]);
        },
        onError: (error: any) => {
          const isTimeout = error?.code === 'ECONNABORTED' || error?.message?.toLowerCase().includes('timeout');
          setMessages(prev => [...prev, { 
            role: 'ai', 
            content: isTimeout 
              ? 'Request timed out. The legal retrieval engine took too long to respond. Please try again.' 
              : `Error: ${error.response?.data?.detail || 'Failed to retrieve answer from Q&A service.'}`
          }]);
        }
      }
    );
  };

  return (
    <div className="flex flex-col h-[500px] border border-[var(--border-surface)] rounded-xl overflow-hidden bg-[var(--bg-surface)] shadow-sm">
      <div className="bg-[var(--bg-surface-hover)] p-4 border-b border-[var(--border-surface)] flex justify-between items-center">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-[var(--color-lila-500)]" />
          <h2 className="text-sm font-semibold text-[var(--foreground)]">Matter Q&A Assistant</h2>
        </div>
        <span className="text-xs bg-[var(--color-lila-500)]/10 text-[var(--color-lila-400)] px-2.5 py-1 rounded-full border border-[var(--color-lila-500)]/20 font-medium">MESA Legal Review Profile</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-[var(--color-anthracite-400)] mt-10 text-sm max-w-sm mx-auto">
            Ask any question about this matter. Responses are grounded in uploaded documents and verified legal sources.
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${msg.role === 'user' ? 'bg-[var(--color-anthracite-800)] text-white border border-[var(--color-anthracite-700)] rounded-tr-sm' : 'bg-[var(--bg-surface-hover)] text-[var(--foreground)] border border-[var(--border-surface)] rounded-tl-sm'}`}>
              <p className="leading-relaxed">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[var(--border-surface)]">
                  <span className="text-xs font-semibold text-[var(--color-anthracite-400)] block mb-2 uppercase tracking-wider">Citations</span>
                  <ul className="text-xs space-y-1.5">
                    {msg.citations.map((cit, cIdx) => (
                      <li key={cIdx} className="text-[var(--color-lila-400)] flex items-start gap-1.5">
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
        
        {qaMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-2xl rounded-tl-sm p-4 flex gap-2 items-center">
              <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce"></div>
              <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-75"></div>
              <div className="w-1.5 h-1.5 bg-[var(--color-lila-500)] rounded-full animate-bounce delay-150"></div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-3 bg-[var(--bg-surface)] border-t border-[var(--border-surface)] flex gap-2">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask a question..." 
          className="flex-1 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-xl px-4 py-2 text-sm text-[var(--foreground)] focus:outline-none focus:border-[var(--color-lila-500)] transition-colors placeholder:text-[var(--color-anthracite-500)]"
          disabled={qaMutation.isPending}
        />
        <button 
          type="submit" 
          disabled={qaMutation.isPending || !query.trim()}
          className="bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] disabled:opacity-50 disabled:hover:bg-[var(--color-lila-600)] text-white px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm flex items-center justify-center min-w-[3rem]"
        >
          {qaMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
}
