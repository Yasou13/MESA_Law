'use client'

import { Bell, Check, ChevronDown, LogOut, Menu, UserRound } from 'lucide-react'
import { useSession, signOut } from 'next-auth/react'
import { useLocale, useTranslations } from 'next-intl'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { useQueryClient } from '@tanstack/react-query'

import { useListNotifications } from '@/api/endpoints/notifications/notifications'
import { useListUserFirms } from '@/api/endpoints/default/default'
import { useGetSessionContext, useSetActiveFirm } from '@/api/endpoints/session/session'
import { Button } from '@/components/ui/button'
import { CommandMenu } from '@/components/layout/CommandMenu'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import { localizedHref, pathnameWithoutLocale } from '@/lib/navigation'

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const locale = useLocale() as 'tr' | 'en'
  const t = useTranslations('Shell')
  const navigationT = useTranslations('Navigation')
  const pathname = pathnameWithoutLocale(usePathname())
  const router = useRouter()
  const queryClient = useQueryClient()
  const { data: session } = useSession()
  const { data: firms = [] } = useListUserFirms()
  const { data: context, refetch } = useGetSessionContext()
  const { data: notifications = [] } = useListNotifications()
  const switchFirm = useSetActiveFirm()
  const [firmMenuOpen, setFirmMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const activeFirm = firms.find((firm) => firm.id === context?.tenant_id)
  const unreadCount = notifications.filter((item) => item.status !== 'READ').length
  const segments = pathname.split('/').filter(Boolean)
  const segmentLabel = (segment: string): string => {
    if (segment === 'dashboard') return navigationT('dashboard')
    if (segment === 'matters') return navigationT('matters')
    if (segment === 'documents') return navigationT('documents')
    if (segment === 'reviews') return t('reviews')
    if (segment === 'operations') return navigationT('operations')
    if (segment === 'timeline') return t('timeline')
    if (segment === 'parties') return t('parties')
    if (segment === 'evidence') return t('evidence')
    if (segment === 'qa' || segment === 'ask-mesa') return navigationT('askMesa')
    if (segment === 'research') return t('research')
    if (segment === 'settings') return navigationT('settings')
    if (segment === 'profile') return t('profileSettings')
    return segment
  }

  const handleFirm = (firmId: string) => {
    setFirmMenuOpen(false)
    if (firmId === context?.tenant_id) return
    switchFirm.mutate({ params: { firm_id: firmId } }, {
      onSuccess: async () => {
        queryClient.clear()
        await refetch()
        toast.success(t('firmChanged'))
        router.push(localizedHref(locale, '/dashboard'))
        router.refresh()
      },
      onError: () => toast.error(t('firmChangeError')),
    })
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-border bg-surface px-4 md:px-6">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenMenu} aria-label={t('openMenu')}>
        <Menu className="size-5" />
      </Button>

      <nav aria-label={t('breadcrumb')} className="hidden min-w-0 flex-1 items-center gap-2 text-sm text-foreground-secondary md:flex">
        {segments.map((segment, index) => {
          const isIdentifier = /^[0-9a-f-]{16,}$/i.test(segment)
          const label = isIdentifier ? `${segment.slice(0, 8)}…` : segmentLabel(segment)
          return (
            <span key={`${segment}-${index}`} className="flex min-w-0 items-center gap-2">
              {index > 0 && <span aria-hidden="true" className="text-foreground-muted">/</span>}
              <span className="max-w-48 truncate last:text-foreground">{label}</span>
            </span>
          )
        })}
      </nav>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <div className="hidden w-[min(22rem,28vw)] lg:block"><CommandMenu /></div>

        <div className="relative hidden sm:block">
          <Button variant="outline" size="sm" onClick={() => setFirmMenuOpen((open) => !open)} aria-expanded={firmMenuOpen}>
            <span className="max-w-36 truncate">{activeFirm?.name ?? t('selectFirm')}</span>
            <ChevronDown className="size-3.5" />
          </Button>
          {firmMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 min-w-56 rounded-lg border border-border bg-surface-raised p-1 shadow-sm">
              {firms.map((firm) => (
                <button key={firm.id} type="button" onClick={() => handleFirm(firm.id)} className="flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-subtle">
                  <span className="truncate">{firm.name}</span>
                  {firm.id === context?.tenant_id && <Check className="size-4 text-verified" />}
                </button>
              ))}
            </div>
          )}
        </div>

        <LanguageSwitcher />
        <ThemeToggle />
        <Button variant="ghost" size="icon" render={<Link href={localizedHref(locale, '/notifications')} />} aria-label={navigationT('notifications')} className="relative">
          <Bell className="size-[18px]" />
          {unreadCount > 0 && <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-danger" aria-label={`${unreadCount}`} />}
        </Button>

        <div className="relative">
          <Button variant="ghost" size="icon" onClick={() => setUserMenuOpen((open) => !open)} aria-expanded={userMenuOpen} aria-label={t('userMenu')}>
            <UserRound className="size-[18px]" />
          </Button>
          {userMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-border bg-surface-raised p-1 shadow-sm">
              <div className="border-b border-border-subtle px-3 py-2">
                <p className="truncate text-sm font-medium">{session?.user?.name ?? t('user')}</p>
                <p className="truncate text-xs text-foreground-secondary">{session?.user?.email}</p>
              </div>
              <Link href={localizedHref(locale, '/settings/profile')} onClick={() => setUserMenuOpen(false)} className="mt-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-surface-subtle">
                <UserRound className="size-4" />{t('profileSettings')}
              </Link>
              <button type="button" onClick={() => signOut({ callbackUrl: localizedHref(locale, '/login') })} className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-danger hover:bg-danger-soft">
                <LogOut className="size-4" />{t('signOut')}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
