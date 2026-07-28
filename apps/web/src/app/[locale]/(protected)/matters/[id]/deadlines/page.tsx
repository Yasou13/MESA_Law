'use client'

import { use, useState } from 'react'
import { ArrowLeft, CalendarDays, Clock, AlertCircle, CheckCircle2, ChevronRight, Plus } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function MatterDeadlinesPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const matterId = resolvedParams.id
  
  // Mock deadlines for Phase 21
  const deadlines = [
    { id: '1', title: 'Filing Deadline for Summary Judgment', date: '2026-08-15', status: 'pending', priority: 'high', type: 'Court Deadline' },
    { id: '2', title: 'Response to Interrogatories', date: '2026-08-01', status: 'pending', priority: 'medium', type: 'Discovery' },
    { id: '3', title: 'Initial Disclosures', date: '2026-07-10', status: 'completed', priority: 'high', type: 'Filing' },
  ]

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-2 text-sm text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Matter Overview
      </Link>
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Deadlines & Calendar</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Track important dates, court filings, and statutory limitations.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2">
            <CalendarDays className="w-4 h-4" /> Calendar View
          </Button>
          <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
            <Plus className="w-4 h-4" /> Add Deadline
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-[var(--foreground)] mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-[var(--color-lila-500)]" /> Upcoming Deadlines
          </h2>
          
          <div className="space-y-3">
            {deadlines.map(deadline => (
              <div 
                key={deadline.id} 
                className={`glass-card rounded-xl border p-5 flex items-center gap-4 transition-all hover:border-[var(--color-lila-500)]/30 ${
                  deadline.status === 'completed' 
                    ? 'border-[var(--border-surface)] opacity-70' 
                    : deadline.priority === 'high' 
                      ? 'border-[var(--color-semantic-error)]/20 shadow-[0_0_15px_rgba(239,68,68,0.05)]' 
                      : 'border-[var(--border-surface)]'
                }`}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                  deadline.status === 'completed' 
                    ? 'bg-emerald-500/10 text-emerald-500' 
                    : deadline.priority === 'high'
                      ? 'bg-[var(--color-semantic-error)]/10 text-[var(--color-semantic-error)]'
                      : 'bg-[var(--color-lila-500)]/10 text-[var(--color-lila-500)]'
                }`}>
                  {deadline.status === 'completed' ? <CheckCircle2 className="w-6 h-6" /> : <CalendarDays className="w-6 h-6" />}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-anthracite-400)]">
                      {deadline.type}
                    </span>
                    {deadline.priority === 'high' && deadline.status !== 'completed' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--color-semantic-error)]/10 text-[var(--color-semantic-error)] uppercase tracking-wider">
                        Urgent
                      </span>
                    )}
                  </div>
                  <h3 className={`font-semibold text-lg ${deadline.status === 'completed' ? 'text-[var(--color-anthracite-400)] line-through' : 'text-[var(--foreground)]'}`}>
                    {deadline.title}
                  </h3>
                  <div className="flex items-center gap-4 mt-2">
                    <span className={`text-sm font-medium ${
                      deadline.status === 'completed' 
                        ? 'text-[var(--color-anthracite-500)]' 
                        : deadline.priority === 'high'
                          ? 'text-[var(--color-semantic-error)]'
                          : 'text-[var(--color-lila-400)]'
                    }`}>
                      {new Date(deadline.date).toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' })}
                    </span>
                  </div>
                </div>
                
                <Button variant="ghost" size="icon" className="shrink-0">
                  <ChevronRight className="w-5 h-5 text-[var(--color-anthracite-400)]" />
                </Button>
              </div>
            ))}
          </div>
        </div>
        
        {/* Right Column: AI Analysis */}
        <div className="space-y-6">
          <div className="glass-card rounded-xl border border-[var(--border-surface)] p-6 bg-gradient-to-b from-[var(--color-lila-500)]/5 to-transparent">
            <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-[var(--color-lila-500)]" />
              AI Deadline Analysis
            </h3>
            <p className="text-sm text-[var(--color-anthracite-300)] leading-relaxed mb-4">
              MESA AI has detected 1 conflicting deadline based on the recently uploaded scheduling order.
            </p>
            <div className="bg-[var(--background)] border border-[var(--border-surface)] rounded-lg p-4 mb-4 border-l-2 border-l-[var(--color-semantic-error)]">
              <h4 className="text-sm font-medium text-[var(--foreground)] mb-1">Summary Judgment Conflict</h4>
              <p className="text-xs text-[var(--color-anthracite-400)]">The filing deadline of Aug 15 conflicts with the discovery cutoff date. Consider filing a motion for extension.</p>
            </div>
            <Button className="w-full text-sm" variant="outline">Review Order Document</Button>
          </div>
        </div>
      </div>
    </div>
  )
}
