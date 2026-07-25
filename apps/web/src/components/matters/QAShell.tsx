import React, { useState } from 'react';

export function QAShell() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{role: 'user' | 'ai', content: string, citations?: string[]}[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeoutError, setTimeoutError] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const newQuery = query;
    setMessages(prev => [...prev, { role: 'user', content: newQuery }]);
    setQuery('');
    setLoading(true);
    setTimeoutError(false);

    // Simulate response delay and occasional timeout
    setTimeout(() => {
      if (Math.random() > 0.85) {
        setTimeoutError(true);
        setLoading(false);
        return;
      }

      let responseText = '';
      let citations: string[] = [];

      if (newQuery.toLowerCase().includes('tazminat')) {
        responseText = 'Mevcut belgelere göre ihbar tazminatı talebi için yeterli delil bulunmamaktadır. Ancak kıdem tazminatı şartları oluşmuştur.';
        citations = ['İhtarname (Sayfa 2)', 'Yargıtay 9. HD. 2021/1234 K.'];
      } else {
        responseText = 'Bu konuyla ilgili yüklenen dosyalarda doğrudan bir eşleşme bulunamadı. Lütfen daha spesifik bir soru sorun veya ilgili belgeleri yükleyin.';
      }

      setMessages(prev => [...prev, { role: 'ai', content: responseText, citations }]);
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-[500px] border border-zinc-800 rounded-lg overflow-hidden bg-zinc-950">
      <div className="bg-zinc-900 p-4 border-b border-zinc-800 flex justify-between items-center">
        <h2 className="text-sm font-semibold text-zinc-100">Matter Q&A Assistant</h2>
        <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-1 rounded border border-blue-800/50">MESA Legal Review Profile</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-zinc-500 mt-10 text-sm">
            Ask any question about this matter. Responses are grounded in uploaded documents and verified legal sources.
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-zinc-800 text-zinc-200'}`}>
              <p>{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-zinc-700/50">
                  <span className="text-xs font-semibold text-zinc-400 block mb-1">Citations:</span>
                  <ul className="text-xs space-y-1">
                    {msg.citations.map((cit, cIdx) => (
                      <li key={cIdx} className="text-blue-300">• {cit}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-zinc-800 rounded-lg p-4 flex gap-2 items-center">
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-75"></div>
              <div className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce delay-150"></div>
            </div>
          </div>
        )}

        {timeoutError && (
          <div className="flex justify-center my-2">
            <div className="bg-red-900/30 text-red-400 text-xs px-3 py-2 rounded border border-red-800/50">
              Request timed out. The legal retrieval engine took too long to respond. Please try again.
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-3 bg-zinc-900 border-t border-zinc-800 flex gap-2">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask a question..." 
          className="flex-1 bg-zinc-950 border border-zinc-700 rounded-lg px-4 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
          disabled={loading}
        />
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
