'use client'

import { useState } from 'react'
import { Database, Zap, Shield, Save } from 'lucide-react'
import { toast } from 'react-hot-toast'

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false)
  const [settings, setSettings] = useState({
    rag_source_package: 'default_tr_corpus',
    intelligence_mode: 'fast',
    auto_quarantine: true,
  })

  const handleSave = () => {
    setIsSaving(true)
    // Simulate API call for pilot
    setTimeout(() => {
      setIsSaving(false)
      toast.success('Settings saved successfully')
    }, 600)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Organization Settings</h1>
        <p className="text-zinc-400">Configure MESA Core integration and workspace preferences.</p>
      </div>

      <div className="space-y-6">
        {/* MESA Core Settings */}
        <section className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface-hover)]">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Database className="w-5 h-5 text-[var(--color-lila-400)]" />
              MESA Core Integration
            </h2>
          </div>
          <div className="p-6 space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--foreground)] block">
                RAG Source Package
              </label>
              <select 
                value={settings.rag_source_package}
                onChange={(e) => setSettings({ ...settings, rag_source_package: e.target.value })}
                className="w-full max-w-md bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg py-2.5 px-3 focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)] text-sm"
              >
                <option value="default_tr_corpus">Mevzuat + Yargıtay Kararları (Türkiye)</option>
                <option value="custom_firm_corpus">Firm Knowledge Base Only</option>
                <option value="hybrid">Hybrid (Global + Internal)</option>
              </select>
              <p className="text-xs text-zinc-500">Determines the context boundary for AI QA operations.</p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--foreground)] block">
                Intelligence Engine Mode
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="radio" 
                    name="intelligence_mode" 
                    value="fast"
                    checked={settings.intelligence_mode === 'fast'}
                    onChange={(e) => setSettings({ ...settings, intelligence_mode: e.target.value })}
                    className="text-[var(--color-lila-500)] focus:ring-[var(--color-lila-500)] bg-[var(--bg-surface-hover)] border-[var(--border-surface)]"
                  />
                  <span className="text-sm flex items-center gap-1"><Zap className="w-3 h-3 text-amber-400" /> Fast (GPT-3.5 Class)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="radio" 
                    name="intelligence_mode" 
                    value="accurate"
                    checked={settings.intelligence_mode === 'accurate'}
                    onChange={(e) => setSettings({ ...settings, intelligence_mode: e.target.value })}
                    className="text-[var(--color-lila-500)] focus:ring-[var(--color-lila-500)] bg-[var(--bg-surface-hover)] border-[var(--border-surface)]"
                  />
                  <span className="text-sm">Accurate (GPT-4 Class)</span>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Security Settings */}
        <section className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
          <div className="px-6 py-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface-hover)]">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-400" />
              Security & Scanning
            </h2>
          </div>
          <div className="p-6">
            <label className="flex items-start gap-3 cursor-pointer">
              <input 
                type="checkbox" 
                checked={settings.auto_quarantine}
                onChange={(e) => setSettings({ ...settings, auto_quarantine: e.target.checked })}
                className="mt-1 rounded text-[var(--color-lila-500)] focus:ring-[var(--color-lila-500)] bg-[var(--bg-surface-hover)] border-[var(--border-surface)]"
              />
              <div>
                <span className="text-sm font-medium text-[var(--foreground)] block">Auto-Quarantine Infected Files</span>
                <span className="text-xs text-zinc-500">Automatically isolate uploaded documents that fail ClamAV or YARA malware scans.</span>
              </div>
            </label>
          </div>
        </section>

        <div className="flex justify-end pt-4">
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-6 py-2.5 bg-[var(--color-lila-500)] text-white rounded-lg hover:bg-[var(--color-lila-600)] transition-colors font-medium text-sm disabled:opacity-50 shadow-lg shadow-[var(--color-lila-500)]/20"
          >
            {isSaving ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}
