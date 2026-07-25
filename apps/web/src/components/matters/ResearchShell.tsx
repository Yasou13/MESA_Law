import React, { useState } from 'react';

export function ResearchShell() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setSearched(true);
    
    setTimeout(() => {
      setResults([
        {
          id: 1,
          type: 'Legislation',
          title: 'Türk Borçlar Kanunu - Madde 417',
          snippet: 'İşveren, hizmet ilişkisinde işçinin kişiliğini korumak ve saygı göstermek, işyerinde dürüstlük ilkelerine uygun bir düzeni sağlamakla yükümlüdür...',
          matchScore: 92
        },
        {
          id: 2,
          type: 'Case Law',
          title: 'Yargıtay 9. Hukuk Dairesi - 2021/456 K.',
          snippet: 'Davacının fazla çalışma ücreti taleplerinin reddine karar verilmiş ise de, sunulan puantaj kayıtları incelendiğinde...',
          matchScore: 85
        }
      ]);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6 text-zinc-100">Legal Research Workspace</h2>
      
      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search legislation, case law, or internal precedents..." 
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
          disabled={loading}
        />
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-6 py-3 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {loading && (
        <div className="space-y-4">
          <div className="h-4 bg-zinc-800 rounded w-1/4 animate-pulse mb-6"></div>
          {[1, 2].map(i => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 p-5 rounded-lg animate-pulse">
              <div className="h-4 bg-zinc-800 rounded w-1/2 mb-3"></div>
              <div className="h-3 bg-zinc-800 rounded w-full mb-2"></div>
              <div className="h-3 bg-zinc-800 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      )}

      {!loading && searched && results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-zinc-400 mb-2">Results</h3>
          {results.map((res) => (
            <div key={res.id} className="bg-zinc-900 border border-zinc-800 p-5 rounded-lg hover:border-zinc-700 transition-colors cursor-pointer">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${res.type === 'Legislation' ? 'bg-purple-900/30 text-purple-400' : 'bg-orange-900/30 text-orange-400'}`}>
                    {res.type}
                  </span>
                  <h4 className="text-zinc-100 font-medium">{res.title}</h4>
                </div>
                <span className="text-xs text-green-400 font-medium bg-green-900/20 px-2 py-1 rounded">
                  Match: {res.matchScore}%
                </span>
              </div>
              <p className="text-sm text-zinc-400 leading-relaxed">{res.snippet}</p>
            </div>
          ))}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center py-12 text-zinc-500">
          No matching legal sources found for your query.
        </div>
      )}

      {!searched && (
        <div className="text-center py-12 text-zinc-600">
          Search across the entire legal database grounded in your current matter context.
        </div>
      )}
    </div>
  );
}
