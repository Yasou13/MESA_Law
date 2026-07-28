'use client'

import { use, useState } from 'react'
import { ArrowLeft, Save, Bot, Download, FileText, ChevronRight, PenTool, CheckCircle2, MessageSquare, Sparkles } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/ui/status-badge'
import { Input } from '@/components/ui/input'
import { ExportApprovalDialog } from '@/features/drafts/components/ExportApprovalDialog'

export default function DraftStudioPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const draftId = resolvedParams.id
  
  // UI Stub for Phase 23
  const [content, setContent] = useState(`IN THE UNITED STATES DISTRICT COURT
FOR the DISTRICT of [STATE]

SMITH ENTERPRISES, INC.,
Plaintiff,

v.

JONES TECHNOLOGY LLC,
Defendant.

CASE NO. 1:26-CV-00123

MOTION FOR SUMMARY JUDGMENT
---------------------------
Plaintiff Smith Enterprises, Inc. ("Smith") respectfully moves this Court pursuant to Federal Rule of Civil Procedure 56 for summary judgment on all claims asserted against Defendant Jones Technology LLC ("Jones").

I. INTRODUCTION
This case involves the clear and undisputed breach of a confidentiality agreement...`)

  const [aiInput, setAiInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleAiAction = (e: React.FormEvent) => {
    e.preventDefault()
    if (!aiInput.trim()) return
    setIsGenerating(true)
    setTimeout(() => {
      setIsGenerating(false)
      setAiInput('')
    }, 1500)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-[var(--background)] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)] flex justify-between items-center shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/drafts" className="text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-px h-6 bg-[var(--border-surface)]"></div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-[var(--foreground)]">Motion for Summary Judgment</h1>
              <StatusBadge status="processing" label="IN PROGRESS" />
            </div>
            <p className="text-xs text-[var(--color-anthracite-500)] mt-0.5">Matter: Smith v. Jones (IP Dispute) • Last saved: Just now</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" /> Export PDF
          </Button>
          <ExportApprovalDialog />
          <Button className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
            <Save className="w-4 h-4" /> Save Draft
          </Button>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        
        {/* Editor Area */}
        <div className="flex-1 flex flex-col bg-[var(--bg-surface-hover)] p-6 overflow-y-auto">
          <div className="max-w-4xl mx-auto w-full flex-1 flex flex-col glass-card border border-[var(--border-surface)] shadow-sm rounded-xl overflow-hidden">
            <div className="border-b border-[var(--border-surface)] p-2 bg-[var(--bg-surface)] flex gap-1">
              <Button variant="ghost" size="sm" className="h-8">B</Button>
              <Button variant="ghost" size="sm" className="h-8 italic">I</Button>
              <Button variant="ghost" size="sm" className="h-8 underline">U</Button>
              <div className="w-px h-6 bg-[var(--border-surface)] mx-1 my-auto"></div>
              <Button variant="ghost" size="sm" className="h-8">H1</Button>
              <Button variant="ghost" size="sm" className="h-8">H2</Button>
            </div>
            <textarea
              className="flex-1 w-full bg-[var(--background)] p-8 resize-none focus:outline-none text-[var(--foreground)] font-serif leading-relaxed"
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Start typing your draft..."
            />
          </div>
        </div>

        {/* Right Panel: AI Co-Pilot */}
        <div className="w-80 border-l border-[var(--border-surface)] bg-[var(--bg-surface)] flex flex-col shrink-0">
          <div className="p-4 border-b border-[var(--border-surface)] flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[var(--color-lila-500)]" />
            <h2 className="font-semibold text-[var(--foreground)]">MESA Co-Pilot</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">Suggested Actions</h3>
              <button className="w-full text-left p-3 rounded-lg border border-[var(--border-surface)] hover:bg-[var(--bg-surface-hover)] transition-colors group">
                <div className="flex items-center gap-2 mb-1 text-[var(--foreground)] font-medium group-hover:text-[var(--color-lila-500)]">
                  <FileText className="w-4 h-4" /> Expand Section II
                </div>
                <p className="text-xs text-[var(--color-anthracite-500)]">Add factual background based on evidence matrix.</p>
              </button>
              <button className="w-full text-left p-3 rounded-lg border border-[var(--border-surface)] hover:bg-[var(--bg-surface-hover)] transition-colors group">
                <div className="flex items-center gap-2 mb-1 text-[var(--foreground)] font-medium group-hover:text-[var(--color-lila-500)]">
                  <CheckCircle2 className="w-4 h-4" /> Cite Check
                </div>
                <p className="text-xs text-[var(--color-anthracite-500)]">Verify 3 references against uploaded case law.</p>
              </button>
            </div>

            <div className="border-t border-[var(--border-surface)] pt-6 space-y-3">
              <h3 className="text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider">Matter Context</h3>
              <div className="p-3 bg-[var(--bg-surface-hover)] rounded-lg">
                <h4 className="text-sm font-medium text-[var(--foreground)] mb-1">Key Claims</h4>
                <ul className="text-xs text-[var(--color-anthracite-500)] list-disc pl-4 space-y-1">
                  <li>Breach of NDA (High Conf)</li>
                  <li>Misappropriation of Trade Secrets</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-[var(--border-surface)] bg-[var(--bg-surface-hover)]">
            <form onSubmit={handleAiAction} className="space-y-3">
              <label className="text-xs font-medium text-[var(--color-anthracite-400)]">Ask AI to modify or generate text:</label>
              <div className="relative">
                <Input 
                  type="text" 
                  placeholder="e.g. Draft an introduction paragraph..."
                  value={aiInput}
                  onChange={e => setAiInput(e.target.value)}
                  className="pr-10 bg-[var(--background)]"
                  disabled={isGenerating}
                />
                <Button 
                  type="submit" 
                  variant="ghost" 
                  size="icon-sm" 
                  className="absolute right-1 top-1/2 -translate-y-1/2 text-[var(--color-lila-500)] hover:text-[var(--color-lila-600)]"
                  disabled={isGenerating || !aiInput.trim()}
                >
                  {isGenerating ? <div className="w-4 h-4 rounded-full border-2 border-[var(--color-lila-500)] border-t-transparent animate-spin"></div> : <Sparkles className="w-4 h-4" />}
                </Button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  )
}
