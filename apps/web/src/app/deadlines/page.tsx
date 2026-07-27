"use client";

import React, { useState } from "react";
import { deadlineAPI } from "../../services/api";

export default function DeadlinesPage() {
  const [loading, setLoading] = useState(false);

  const fetchDeadlines = async () => {
    setLoading(true);
    try {
      await deadlineAPI.listPotentialDeadlines("test-matter-id");
      alert("Listelendi (Mock).");
    } catch (err) {
      console.error(err);
      alert("Hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Deadline Management</h1>
      <p className="mb-4 text-gray-600">Olası süreleri onaylayın veya reddedin.</p>
      
      <button 
        onClick={fetchDeadlines}
        disabled={loading}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
      >
        {loading ? "Yükleniyor..." : "Süreleri Getir"}
      </button>

      <div className="mt-8">
        <div className="bg-gray-100 p-4 rounded text-center text-sm text-gray-500">
          Onay bekleyen süre bulunamadı.
        </div>
      </div>
    </div>
  );
}
