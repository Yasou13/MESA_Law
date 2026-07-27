"use client";

import React, { useState } from "react";
import { qaAPI } from "../../services/api";

export default function QAPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question) return;
    setLoading(true);
    setResponse(null);
    try {
      const res = await qaAPI.askQuestion("test-matter-id", question);
      setResponse(res);
    } catch (err) {
      console.error(err);
      alert("Hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Matter Q&A</h1>
      <p className="mb-4 text-gray-600">Dosya üzerindeki dökümanlara soru sorun.</p>
      
      <form onSubmit={handleAsk} className="flex gap-2 mb-8">
        <input 
          type="text" 
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Sorunuzu yazın..."
          className="border p-2 rounded flex-1"
        />
        <button 
          type="submit"
          disabled={loading || !question}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? "Soruluyor..." : "Soru Sor"}
        </button>
      </form>

      {response && (
        <div className="bg-gray-50 border p-4 rounded">
          <h2 className="font-semibold mb-2">Cevap:</h2>
          <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
