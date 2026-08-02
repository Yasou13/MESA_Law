'use client'

import { Clock3, Database, Shield } from 'lucide-react'
import { useTranslations } from 'next-intl'

import { useGetSystemSettings } from '@/api/endpoints/system/system'
import { ErrorState, LoadingState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import { StatusBadge } from '@/components/ui/status-badge'

export default function AdminSettingsPage() {
  const t = useTranslations('SystemSettings')
  const common = useTranslations('Common')
  const settingsQuery = useGetSystemSettings()

  if (settingsQuery.isLoading) return <LoadingState label={common('loading')} />
  if (settingsQuery.isError || !settingsQuery.data) return <ErrorState title={t('loadError')} description={t('loadErrorDescription')} onRetry={() => settingsQuery.refetch()} />

  const settings = settingsQuery.data
  const features = [
    [t('documentScanning'), settings.features.document_ocr_enabled],
    [t('mesaRebuild'), settings.features.mesa_rebuild_enabled],
    [t('externalResearch'), settings.features.external_research_enabled],
    [t('drafting'), settings.features.drafting_ai_enabled],
    [t('deadlineAi'), settings.features.deadline_ai_enabled],
  ] as const

  return (
    <div className="space-y-6">
      <PageHeader title={t('title')} description={t('description')} />

      <Panel>
        <PanelHeader><h2 className="flex items-center gap-2 font-semibold"><Database className="size-4 text-primary-content" />{t('features')}</h2></PanelHeader>
        <PanelBody className="divide-y divide-border-subtle py-0">
          {features.map(([name, enabled]) => (
            <div key={name} className="flex items-start justify-between gap-4 py-4">
              <div><p className="font-medium">{name}</p>{!enabled && <p className="mt-1 text-xs text-foreground-muted">{t('unavailableNote')}</p>}</div>
              <StatusBadge status={enabled ? 'success' : 'degraded'} label={enabled ? t('enabled') : t('unavailable')} />
            </div>
          ))}
        </PanelBody>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel>
          <PanelHeader><h2 className="flex items-center gap-2 font-semibold"><Shield className="size-4 text-primary-content" />{t('authPolicy')}</h2></PanelHeader>
          <PanelBody>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between gap-4"><dt className="text-foreground-secondary">{t('mfa')}</dt><dd className="font-medium">{settings.security.require_mfa ? t('yes') : t('no')}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-foreground-secondary">{t('sessionTimeout')}</dt><dd className="font-medium">{t('minutes', { value: settings.security.session_timeout_minutes })}</dd></div>
            </dl>
            <p className="mt-5 text-xs leading-5 text-foreground-muted">{t('authNote')}</p>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader><h2 className="flex items-center gap-2 font-semibold"><Clock3 className="size-4 text-primary-content" />{t('retention')}</h2></PanelHeader>
          <PanelBody>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between gap-4"><dt className="text-foreground-secondary">{t('auditLog')}</dt><dd className="font-medium">{t('days', { value: settings.retention.audit_log_days })}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-foreground-secondary">{t('deletedMarker')}</dt><dd className="font-medium">{t('days', { value: settings.retention.deleted_document_days })}</dd></div>
            </dl>
            <p className="mt-5 text-xs leading-5 text-foreground-muted">{t('retentionNote')}</p>
          </PanelBody>
        </Panel>
      </div>
    </div>
  )
}
