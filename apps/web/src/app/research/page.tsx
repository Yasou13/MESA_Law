"use client";

import React, { useState } from "react";
import { researchAPI } from "../../services/api";

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      await researchAPI.startResearch("test-matter-id", query);
      alert("Araştırma başlatıldı. Sonuçlar Review Queue'ya düşecektir.");
    } catch (err) {
      console.error(err);
      alert("Hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Legal Research</h1>
      <p className="mb-4 text-gray-600">Mevzuat ve içtihat araması yapın.</p>
      
      <form onSubmit={handleSearch} className="flex gap-2">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Arama terimi girin..."
          className="border p-2 rounded flex-1"
        />
        <button 
          type="submit"
          disabled={loading || !query}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Aranıyor..." : "Ara"}
        </button>
      </form>
    </div>
  );
}
