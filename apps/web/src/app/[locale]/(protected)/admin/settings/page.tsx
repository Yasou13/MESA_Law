'use client'

import { AlertTriangle, CheckCircle2, Clock, Database, Loader2, Shield } from 'lucide-react'

import { useGetSystemSettings } from '@/api/endpoints/system/system'

export default function AdminSettingsPage() {
  const { data: settings, isLoading, isError } = useGetSystemSettings()

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] flex-1 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--color-lila-500)]" />
      </div>
    )
  }

  if (isError || !settings) {
    return (
      <div className="mx-auto max-w-4xl p-8">
        <div className="flex gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-5 text-red-400">
          <AlertTriangle className="h-5 w-5 shrink-0" /> System settings could not be loaded.
        </div>
      </div>
    )
  }

  const features = [
    ['Document scanning and extraction', settings.features.document_ocr_enabled],
    ['MESA rebuild', settings.features.mesa_rebuild_enabled],
    ['External legal research', settings.features.external_research_enabled],
    ['AI draft generation', settings.features.drafting_ai_enabled],
    ['Deadline AI', settings.features.deadline_ai_enabled],
  ] as const

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6 lg:p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">Runtime configuration</h1>
        <p className="mt-1 text-[var(--color-anthracite-500)]">
          Read-only effective settings. Runtime mutation is intentionally unavailable in this MVP.
        </p>
      </div>

      <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <Database className="h-5 w-5 text-[var(--color-lila-500)]" /> Feature availability
        </h2>
        <div className="mt-5 divide-y divide-[var(--border-surface)]">
          {features.map(([name, enabled]) => (
            <div key={name} className="flex items-center justify-between gap-4 py-4">
              <div>
                <p className="font-medium">{name}</p>
                {!enabled && (
                  <p className="mt-1 text-xs text-[var(--color-anthracite-500)]">
                    Unavailable; the UI will not queue or simulate this capability.
                  </p>
                )}
              </div>
              <span
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                  enabled
                    ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-500'
                    : 'border-amber-500/20 bg-amber-500/10 text-amber-500'
                }`}
              >
                {enabled ? 'ENABLED' : 'UNAVAILABLE'}
              </span>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Shield className="h-5 w-5 text-[var(--color-lila-500)]" /> Authentication policy
          </h2>
          <dl className="mt-5 space-y-4 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-[var(--color-anthracite-400)]">MFA required</dt>
              <dd className="flex items-center gap-1 font-medium">
                {settings.security.require_mfa && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                {settings.security.require_mfa ? 'Yes' : 'No'}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-[var(--color-anthracite-400)]">Session timeout</dt>
              <dd className="font-medium">{settings.security.session_timeout_minutes} minutes</dd>
            </div>
          </dl>
          <p className="mt-5 text-xs leading-relaxed text-[var(--color-anthracite-500)]">
            Identity policy is administered in Keycloak. This page does not claim certification or cryptographic controls beyond what the running deployment reports.
          </p>
        </section>

        <section className="glass-card rounded-xl border border-[var(--border-surface)] p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Clock className="h-5 w-5 text-[var(--color-lila-500)]" /> Retention values
          </h2>
          <dl className="mt-5 space-y-4 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-[var(--color-anthracite-400)]">Audit log</dt>
              <dd className="font-medium">{settings.retention.audit_log_days} days</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-[var(--color-anthracite-400)]">Deleted document marker</dt>
              <dd className="font-medium">{settings.retention.deleted_document_days} days</dd>
            </div>
          </dl>
          <p className="mt-5 text-xs leading-relaxed text-[var(--color-anthracite-500)]">
            These are effective configuration values, not evidence that a scheduled deletion job has run.
          </p>
        </section>
      </div>
    </div>
  )
}
