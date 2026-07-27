"use client";

import React, { useState } from "react";
import { draftAPI } from "../../services/api";

export default function DraftsPage() {
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Mock matter ID for demonstration
      await draftAPI.generateDraft("test-matter-id", "Standart Dilekçe");
      alert("Taslak oluşturma işlemi sıraya alındı.");
    } catch (e) {
      console.error(e);
      alert("Hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Draft Studio</h1>
      <p className="mb-4 text-gray-600">Taslak üretimi ve yönetimi ekranı.</p>
      
      <button 
        onClick={handleGenerate}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Üretiliyor..." : "Yeni Taslak Üret"}
      </button>

      <div className="mt-8 border-t pt-4">
        <h2 className="text-xl font-semibold mb-2">Mevcut Taslaklar</h2>
        <div className="bg-gray-100 p-4 rounded text-center text-sm text-gray-500">
          Henüz taslak bulunmuyor.
        </div>
      </div>
    </div>
  );
}
