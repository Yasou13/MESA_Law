'use client'

import { Loader2, Mail, Save, Shield, User } from 'lucide-react'
import { useLocale, useTranslations } from 'next-intl'
import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

import { useGetCurrentUserProfile, useUpdateCurrentUserProfile } from '@/api/endpoints/users/users'
import { LoadingState } from '@/components/ui/async-state'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/ui/page-header'
import { Panel, PanelBody, PanelHeader } from '@/components/ui/panel'
import type { AppLocale } from '@/lib/navigation'

export default function ProfilePage() {
  const t = useTranslations('Profile')
  const common = useTranslations('Common')
  const locale = useLocale() as AppLocale
  const profileQuery = useGetCurrentUserProfile()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    if (!profileQuery.data) return
    setFullName(profileQuery.data.full_name)
    setEmail(profileQuery.data.email)
  }, [profileQuery.data])

  const updateProfile = useUpdateCurrentUserProfile({
    mutation: {
      onSuccess: () => {
        toast.success(t('saved'))
        setIsDirty(false)
        profileQuery.refetch()
      },
      onError: () => toast.error(t('saveError')),
    },
  })

  if (profileQuery.isLoading) return <LoadingState label={common('loading')} />
  const profile = profileQuery.data

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        description={t('description')}
        actions={
          <Button onClick={() => updateProfile.mutate({ data: { full_name: fullName, email } })} disabled={!isDirty || updateProfile.isPending}>
            {updateProfile.isPending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            {updateProfile.isPending ? common('saving') : t('save')}
          </Button>
        }
      />

      <Panel>
        <PanelHeader className="justify-start gap-4">
          <div className="flex size-12 items-center justify-center rounded-full border border-primary/25 bg-primary-soft text-lg font-semibold text-primary" aria-hidden="true">
            {profile?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="min-w-0"><h2 className="truncate font-semibold">{profile?.full_name || 'User'}</h2><p className="truncate text-xs text-foreground-secondary">{profile?.roles?.join(', ') || t('noRoles')}</p></div>
        </PanelHeader>
        <PanelBody className="space-y-6">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="space-y-2 text-sm font-medium">
              <span className="flex items-center gap-2"><User className="size-4 text-foreground-muted" />{t('fullName')}</span>
              <Input value={fullName} onChange={(event) => { setFullName(event.target.value); setIsDirty(true) }} autoComplete="name" />
            </label>
            <label className="space-y-2 text-sm font-medium">
              <span className="flex items-center gap-2"><Mail className="size-4 text-foreground-muted" />{t('email')}</span>
              <Input type="email" value={email} onChange={(event) => { setEmail(event.target.value); setIsDirty(true) }} autoComplete="email" />
            </label>
          </div>

          {profile?.is_support_access_granted && profile.support_access_granted_until && (
            <div className="flex gap-3 rounded-md border border-warning/30 bg-warning-soft p-4 text-sm">
              <Shield className="mt-0.5 size-5 shrink-0 text-warning" />
              <div><h3 className="font-semibold text-warning">{t('supportTitle')}</h3><p className="mt-1 text-foreground-secondary">{t('supportDescription', { until: new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeStyle: 'short' }).format(new Date(profile.support_access_granted_until)) })}</p></div>
            </div>
          )}
        </PanelBody>
      </Panel>
    </div>
  )
}
