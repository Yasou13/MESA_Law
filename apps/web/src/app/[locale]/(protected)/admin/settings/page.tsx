'use client'

import { useState } from 'react'
import { Settings, Building2, Sliders, Shield, Database, Save, Server, Loader2, Sparkles, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'

// UI Stub for Phase 29
export default function AdminSettingsPage() {
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'firm' | 'ai' | 'security'>('firm')

  const handleSave = () => {
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
    }, 1500)
  }

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">System Settings</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage firm-wide configuration, AI models, and security policies.</p>
        </div>
        <Button onClick={handleSave} disabled={isSaving} className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
          {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Navigation Sidebar */}
        <div className="w-full md:w-64 shrink-0 space-y-2">
          <button 
            onClick={() => setActiveTab('firm')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'firm' 
                ? 'bg-[var(--color-lila-500)]/10 text-[var(--color-lila-500)]' 
                : 'text-[var(--color-anthracite-400)] hover:bg-[var(--bg-surface-hover)]'
            }`}
          >
            <Building2 className="w-5 h-5" /> Firm Profile
          </button>
          <button 
            onClick={() => setActiveTab('ai')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'ai' 
                ? 'bg-[var(--color-lila-500)]/10 text-[var(--color-lila-500)]' 
                : 'text-[var(--color-anthracite-400)] hover:bg-[var(--bg-surface-hover)]'
            }`}
          >
            <Sparkles className="w-5 h-5" /> AI & Models
          </button>
          <button 
            onClick={() => setActiveTab('security')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'security' 
                ? 'bg-[var(--color-lila-500)]/10 text-[var(--color-lila-500)]' 
                : 'text-[var(--color-anthracite-400)] hover:bg-[var(--bg-surface-hover)]'
            }`}
          >
            <Shield className="w-5 h-5" /> Security & Compliance
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 space-y-6">
          
          {activeTab === 'firm' && (
            <div className="glass-card rounded-xl border border-[var(--border-surface)] p-6 space-y-6">
              <h2 className="text-xl font-semibold text-[var(--foreground)] border-b border-[var(--border-surface)] pb-4 mb-6">
                Firm Details
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="firmName" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Firm Name</label>
                  <Input id="firmName" defaultValue="MESA Law Partners" className="bg-[var(--background)] border-[var(--border-surface)]" />
                </div>
                <div className="space-y-2">
                  <label htmlFor="domain" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Primary Domain</label>
                  <Input id="domain" defaultValue="mesalaw.com" className="bg-[var(--background)] border-[var(--border-surface)]" />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label htmlFor="address" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Headquarters Address</label>
                  <Input id="address" defaultValue="1200 Legal Avenue, Suite 400, New York, NY 10001" className="bg-[var(--background)] border-[var(--border-surface)]" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="glass-card rounded-xl border border-[var(--border-surface)] p-6 space-y-6">
              <h2 className="text-xl font-semibold text-[var(--foreground)] border-b border-[var(--border-surface)] pb-4 mb-6 flex items-center gap-2">
                AI Engine Configuration
              </h2>
              
              <div className="space-y-8">
                <div className="space-y-4">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Primary LLM Provider</label>
                  <Select defaultValue="mesa-claude">
                    <SelectTrigger className="w-full md:w-[400px] bg-[var(--background)] border-[var(--border-surface)]">
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mesa-claude">Anthropic Claude 3.5 Sonnet (MESA Secured)</SelectItem>
                      <SelectItem value="mesa-gpt4">OpenAI GPT-4o (MESA Secured)</SelectItem>
                      <SelectItem value="mesa-local">Llama 3 70B (On-Premise)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-[var(--color-anthracite-500)] mt-2">
                    This model powers drafting, analysis, and global Q&A. All selected models comply with SOC2 data retention policies.
                  </p>
                </div>

                <div className="space-y-4 pt-6 border-t border-[var(--border-surface)]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-base font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Auto-Extraction on Upload</label>
                      <p className="text-sm text-[var(--color-anthracite-500)] mt-1 max-w-lg">
                        Automatically extract entities, claims, and dates from documents the moment they are uploaded.
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="space-y-4 pt-6 border-t border-[var(--border-surface)]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-base font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Internet-Enabled Research</label>
                      <p className="text-sm text-[var(--color-anthracite-500)] mt-1 max-w-lg">
                        Allow the AI agent to browse public court dockets and news sites when internal knowledge is insufficient.
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="glass-card rounded-xl border border-[var(--border-surface)] p-6 space-y-6">
              <h2 className="text-xl font-semibold text-[var(--foreground)] border-b border-[var(--border-surface)] pb-4 mb-6 flex items-center gap-2">
                Security & Access Control
              </h2>
              
              <div className="space-y-6">
                <div className="flex items-start gap-4 p-4 rounded-xl border border-[var(--color-semantic-success)]/20 bg-[var(--color-semantic-success)]/5">
                  <CheckCircle2 className="w-6 h-6 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-[var(--foreground)]">SOC2 Compliance Active</h3>
                    <p className="text-sm text-[var(--color-anthracite-400)] mt-1">
                      Data is encrypted at rest (AES-256) and in transit (TLS 1.3). Zero data is used for training foundation models.
                    </p>
                  </div>
                </div>

                <div className="space-y-4 pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-base font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Require Multi-Factor Authentication (MFA)</label>
                      <p className="text-sm text-[var(--color-anthracite-500)] mt-1">Enforce MFA for all firm members across all devices.</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="space-y-4 pt-6 border-t border-[var(--border-surface)]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-base font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Strict Ethical Wall Enforcement</label>
                      <p className="text-sm text-[var(--color-anthracite-500)] mt-1">Prevent search cross-contamination between restricted matters.</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>

                <div className="space-y-4 pt-6 border-t border-[var(--border-surface)]">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-base font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Allow Anonymous Telemetry</label>
                      <p className="text-sm text-[var(--color-anthracite-500)] mt-1">Share anonymized usage data to help MESA improve the product. Does not include matter data or prompts.</p>
                    </div>
                    <Switch defaultChecked={false} />
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
