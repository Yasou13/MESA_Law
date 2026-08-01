'use client'

import { Bell, Check, ChevronDown, LogOut, Menu, UserRound } from 'lucide-react'
import { useSession, signOut } from 'next-auth/react'
import { useLocale } from 'next-intl'
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
import { localizedHref, pathnameWithoutLocale } from '@/lib/navigation'

function segmentLabel(segment: string, locale: 'tr' | 'en'): string {
  const pair = (tr: string, en: string) => locale === 'tr' ? tr : en
  switch (segment) {
    case 'dashboard': return pair('Gösterge Paneli', 'Dashboard')
    case 'matters': return pair('Dosyalar', 'Matters')
    case 'documents': return pair('Belgeler', 'Documents')
    case 'reviews': return pair('İncelemeler', 'Reviews')
    case 'operations': return pair('Operasyonlar', 'Operations')
    case 'timeline': return 'Timeline'
    case 'parties': return pair('Taraflar', 'Parties')
    case 'evidence': return pair('İddialar ve Deliller', 'Claims and Evidence')
    case 'qa':
    case 'ask-mesa': return 'Ask MESA'
    case 'research': return pair('Hukuki Kaynaklar', 'Legal Sources')
    case 'settings': return pair('Ayarlar', 'Settings')
    case 'profile': return pair('Profil', 'Profile')
    default: return segment
  }
}

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const locale = useLocale() as 'tr' | 'en'
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

  const handleFirm = (firmId: string) => {
    setFirmMenuOpen(false)
    if (firmId === context?.tenant_id) return
    switchFirm.mutate({ params: { firm_id: firmId } }, {
      onSuccess: async () => {
        queryClient.clear()
        await refetch()
        toast.success(locale === 'tr' ? 'Aktif firma değiştirildi' : 'Active firm changed')
        router.push(localizedHref(locale, '/dashboard'))
        router.refresh()
      },
      onError: () => toast.error(locale === 'tr' ? 'Firma değiştirilemedi' : 'Firm could not be changed'),
    })
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-border bg-surface px-4 md:px-6">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onOpenMenu} aria-label={locale === 'tr' ? 'Menüyü aç' : 'Open menu'}>
        <Menu className="size-5" />
      </Button>

      <nav aria-label={locale === 'tr' ? 'İçerik yolu' : 'Breadcrumb'} className="hidden min-w-0 flex-1 items-center gap-2 text-sm text-foreground-secondary md:flex">
        {segments.map((segment, index) => {
          const isIdentifier = /^[0-9a-f-]{16,}$/i.test(segment)
          const label = isIdentifier ? `${segment.slice(0, 8)}…` : segmentLabel(segment, locale)
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
            <span className="max-w-36 truncate">{activeFirm?.name ?? (locale === 'tr' ? 'Firma seçin' : 'Select firm')}</span>
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

        <ThemeToggle />
        <Button variant="ghost" size="icon" render={<Link href={localizedHref(locale, '/notifications')} />} aria-label={locale === 'tr' ? 'Bildirimler' : 'Notifications'} className="relative">
          <Bell className="size-[18px]" />
          {unreadCount > 0 && <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-danger" aria-label={`${unreadCount}`} />}
        </Button>

        <div className="relative">
          <Button variant="ghost" size="icon" onClick={() => setUserMenuOpen((open) => !open)} aria-expanded={userMenuOpen} aria-label={locale === 'tr' ? 'Kullanıcı menüsü' : 'User menu'}>
            <UserRound className="size-[18px]" />
          </Button>
          {userMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-border bg-surface-raised p-1 shadow-sm">
              <div className="border-b border-border-subtle px-3 py-2">
                <p className="truncate text-sm font-medium">{session?.user?.name ?? (locale === 'tr' ? 'Kullanıcı' : 'User')}</p>
                <p className="truncate text-xs text-foreground-secondary">{session?.user?.email}</p>
              </div>
              <Link href={localizedHref(locale, '/settings/profile')} onClick={() => setUserMenuOpen(false)} className="mt-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-surface-subtle">
                <UserRound className="size-4" />{locale === 'tr' ? 'Profil ayarları' : 'Profile settings'}
              </Link>
              <button type="button" onClick={() => signOut({ callbackUrl: localizedHref(locale, '/login') })} className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-danger hover:bg-danger-soft">
                <LogOut className="size-4" />{locale === 'tr' ? 'Çıkış yap' : 'Sign out'}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
