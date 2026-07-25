import React, { useState, useEffect } from 'react';
import axios from 'axios';

type TimelineEvent = {
  id: string | number;
  date: string;
  title: string;
  source: string;
  confidence: string;
};

export function Timeline({ matterId = "1" }: { matterId?: string }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  const fetchTimeline = () => {
    setLoading(true);
    setError(false);
    axios.get(`/api/v1/matters/${matterId}/timeline`)
      .then(res => {
        setEvents(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch timeline:", err);
        setError(true);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchTimeline();
  }, [matterId]);

  if (loading) {
    return (
      <div className="p-8 animate-pulse space-y-6">
        <div className="h-4 bg-zinc-800 rounded w-1/4"></div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-4">
              <div className="w-2 h-full bg-zinc-800 rounded"></div>
              <div className="h-16 bg-zinc-800 rounded w-full"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-red-900/20 border border-red-900 rounded-lg text-red-200">
        <h3 className="font-semibold mb-2">Degraded Source Error</h3>
        <p className="text-sm">Could not load the full timeline. Please try again later.</p>
        <button onClick={fetchTimeline} className="mt-4 text-sm bg-red-800/50 hover:bg-red-800 px-4 py-2 rounded">Retry</button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6 text-zinc-100">Chronological Timeline</h2>
      <div className="relative border-l border-zinc-700 ml-3 space-y-8">
        {events.map((evt) => (
          <div key={evt.id} className="pl-6 relative">
            <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-1.5 top-1.5 ring-4 ring-zinc-950"></div>
            <div className="text-sm text-zinc-400 mb-1">{evt.date}</div>
            <div className="text-zinc-200 font-medium">{evt.title}</div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs px-2 py-1 bg-zinc-800 text-zinc-300 rounded border border-zinc-700">Source: {evt.source}</span>
              <span className={`text-xs px-2 py-1 rounded border ${evt.confidence === 'high' ? 'bg-green-900/30 text-green-400 border-green-800/50' : 'bg-yellow-900/30 text-yellow-400 border-yellow-800/50'}`}>
                Confidence: {evt.confidence}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

