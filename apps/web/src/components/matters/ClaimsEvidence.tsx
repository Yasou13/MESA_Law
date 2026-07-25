import React, { useState, useEffect } from 'react';

export function ClaimsEvidence() {
  const [loading, setLoading] = useState(true);
  const [claims, setClaims] = useState<any[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setClaims([
        {
          id: 1,
          claim: 'Fazla mesai ücretleri ödenmemiştir',
          evidence: 'Banka dekontları, bordrolar (019f99... belge)',
          support: 'strong',
          confidence: 'high'
        },
        {
          id: 2,
          claim: 'Haksız fesih yapılmıştır',
          evidence: 'İhtarname metnindeki gerekçeler',
          support: 'partial',
          confidence: 'medium'
        },
        {
          id: 3,
          claim: 'İhbar tazminatı hakkı doğmuştur',
          evidence: null,
          support: 'none',
          confidence: 'low'
        }
      ]);
      setLoading(false);
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="p-6 animate-pulse space-y-4">
        {[1, 2].map(i => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 p-4 rounded-lg h-24"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6 text-zinc-100">Claims & Evidence</h2>
      <div className="space-y-4">
        {claims.map((claim) => (
          <div key={claim.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 flex flex-col md:flex-row gap-6">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-zinc-400 mb-1">Claim</h3>
              <p className="text-zinc-100">{claim.claim}</p>
              <div className="mt-3">
                <span className={`text-xs px-2 py-1 rounded border ${claim.confidence === 'high' ? 'bg-green-900/30 text-green-400 border-green-800/50' : claim.confidence === 'medium' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800/50' : 'bg-red-900/30 text-red-400 border-red-800/50'}`}>
                  Confidence: {claim.confidence}
                </span>
              </div>
            </div>
            
            <div className="w-px bg-zinc-800 hidden md:block"></div>
            
            <div className="flex-1">
              <h3 className="text-sm font-medium text-zinc-400 mb-1">Evidence & Support</h3>
              {claim.evidence ? (
                <p className="text-zinc-300 text-sm">{claim.evidence}</p>
              ) : (
                <p className="text-zinc-500 text-sm italic">No supporting evidence found in uploaded documents</p>
              )}
              <div className="mt-3">
                <span className={`text-xs px-2 py-1 rounded border ${claim.support === 'strong' ? 'bg-blue-900/30 text-blue-400 border-blue-800/50' : claim.support === 'partial' ? 'bg-orange-900/30 text-orange-400 border-orange-800/50' : 'bg-zinc-800 text-zinc-400 border-zinc-700'}`}>
                  Support: {claim.support}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
