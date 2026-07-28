'use client'

import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { FolderOpen, Search, LogOut, CheckSquare, LayoutDashboard, Settings, Users, Bell, FileText, Clock, FileEdit, ChevronDown, Check, Menu, X, FileCheck } from 'lucide-react'
import { clsx } from 'clsx'
import { signOut, useSession } from 'next-auth/react'
import { CommandMenu } from './CommandMenu'
import { useGetNotificationsApiV1NotificationsGet } from '@/api/endpoints/notifications/notifications'
import { useListUserFirms } from '@/api/endpoints/default/default'
import { useSetActiveFirmApiV1SessionActiveFirmPost } from '@/api/endpoints/session/session'
import { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { useTranslations } from 'next-intl'
import { LanguageSwitcher } from './LanguageSwitcher'
import { useQueryClient } from '@tanstack/react-query'

const navigation = [
  { nameKey: 'dashboard', href: '/dashboard', icon: LayoutDashboard },
  { nameKey: 'matters', href: '/matters', icon: FolderOpen },
  { nameKey: 'documents', href: '/documents', icon: FileText },
  { nameKey: 'review_center', href: '/reviews', icon: FileCheck },
  { nameKey: 'drafts', href: '/drafts', icon: FileEdit },
  { nameKey: 'notifications', href: '/notifications', icon: Bell },
  { nameKey: 'operations', href: '/operations', icon: CheckSquare },
] as const

const adminNavigation = [
  { nameKey: 'members', href: '/admin/members', icon: Users },
  { nameKey: 'audit', href: '/admin/audit', icon: FileText },
  { nameKey: 'settings', href: '/admin/settings', icon: Settings },
] as const

export function Sidebar() {
  const tNav = useTranslations('Navigation')
  const tAdmin = useTranslations('Administration')
  const tSidebar = useTranslations('Sidebar')
  
  const pathname = usePathname()
  const router = useRouter()
  const queryClient = useQueryClient()
  const { data: notifRes } = useGetNotificationsApiV1NotificationsGet()
  const unreadCount = Array.isArray(notifRes?.data)
    ? notifRes.data.filter((n: { status?: string }) => n.status !== 'READ').length
    : 0

  const { data: firmsRes } = useListUserFirms()
  const firms = firmsRes?.data || []
  const { mutate: setActiveFirm, isPending: isSwitching } = useSetActiveFirmApiV1SessionActiveFirmPost()

  const { data: session, update: updateSession } = useSession()
  const [activeFirmId, setActiveFirmId] = useState<string | null>(null)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  useEffect(() => {
    if (session?.activeFirmId) {
      setActiveFirmId(session.activeFirmId as string)
    } else if (firms.length > 0) {
      setActiveFirmId(firms[0].id)
      updateSession({ activeFirmId: firms[0].id })
    }
  }, [firms, session?.activeFirmId, updateSession])

  const handleSwitchFirm = (firmId: string) => {
    setIsDropdownOpen(false)
    if (firmId === activeFirmId) return

    setActiveFirm({ params: { firm_id: firmId } }, {
      onSuccess: async () => {
        await updateSession({ activeFirmId: firmId })
        setActiveFirmId(firmId)
        queryClient.clear() // Phase 2: Clear TanStack Query cache
        toast.success('Switched active firm')
        router.push('/dashboard') // Phase 2: Navigate to dashboard without reload
        router.refresh()
      },
      onError: () => {
        toast.error('Failed to switch firm')
      }
    })
  }

  const activeFirmName = firms.find((f: { id: string; name: string }) => f.id === activeFirmId)?.name || 'MESA Law'

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-[var(--bg-surface)] border-b border-[var(--border-surface)] flex items-center px-4 z-40 justify-between">
        <Link href="/" className="flex items-center gap-2">
          <img src="/icon-192.png" alt="MESA Logo" className="w-8 h-8 rounded-lg shadow-sm" />
          <span className="text-xl font-bold text-[var(--foreground)]">MESA</span>
        </Link>
        <button 
          onClick={() => setIsMobileOpen(true)}
          className="p-2 -mr-2 text-[var(--foreground)]"
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-[var(--background)]/80 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Content */}
      <div className={clsx(
        "flex flex-col w-64 border-r border-[var(--border-surface)] bg-[var(--bg-surface)] backdrop-blur-xl h-screen fixed md:sticky top-0 z-50 transition-transform duration-300 ease-in-out overflow-y-auto",
        isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        {/* Header & Firm Switcher */}
        <div className="p-6 pb-2">
          <div className="flex items-center justify-between mb-6">
            <Link href="/" className="flex items-center gap-2" onClick={() => setIsMobileOpen(false)}>
              <img src="/icon-192.png" alt="MESA Logo" className="w-8 h-8 rounded-lg shadow-sm" />
              <span className="text-xl font-bold text-[var(--foreground)]">MESA</span>
            </Link>
            <button 
              className="md:hidden p-1 text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]"
              onClick={() => setIsMobileOpen(false)}
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Firm Switcher */}
          <div className="relative">
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              disabled={isSwitching}
              className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg text-sm text-[var(--foreground)] hover:border-[var(--color-lila-500)]/50 transition-colors disabled:opacity-50"
            >
              <span className="font-medium truncate mr-2">{isSwitching ? tSidebar('switching') : activeFirmName}</span>
              <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {isDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--bg-surface)] border border-[var(--border-surface)] rounded-lg shadow-xl z-50 overflow-hidden">
                {firms.map((firm: { id: string; name: string }) => (
                  <button
                    key={firm.id}
                    onClick={() => handleSwitchFirm(firm.id)}
                    className="w-full flex items-center justify-between px-3 py-2.5 text-sm text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)] transition-colors text-left"
                  >
                    <span className="truncate">{firm.name}</span>
                    {firm.id === activeFirmId && <Check className="w-4 h-4 text-[var(--color-lila-500)]" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="px-4 mt-6">
          <CommandMenu />
        </div>

        {/* Main Navigation */}
        <nav className="px-4 space-y-1 mt-4">
          {navigation.map((item) => {
            const isActive = pathname.startsWith(item.href)
            return (
              <Link
                key={item.nameKey}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-[var(--color-lila-500)] text-white shadow-md shadow-[var(--color-lila-500)]/20" 
                    : "text-[var(--color-anthracite-500)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]"
                )}
              >
                <item.icon className={clsx("w-5 h-5", isActive ? "text-white" : "text-[var(--color-anthracite-400)]")} />
                {tNav(item.nameKey)}
              </Link>
            )
          })}
        </nav>

        {/* Administration Navigation */}
        <div className="mt-8 px-4">
          <h3 className="px-3 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider mb-2">{tAdmin('title')}</h3>
          <nav className="space-y-1">
            {adminNavigation.map((item) => {
              const isActive = pathname.startsWith(item.href)
              return (
                <Link
                  key={item.nameKey}
                  href={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={clsx(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive 
                      ? "bg-[var(--color-lila-500)] text-white shadow-md shadow-[var(--color-lila-500)]/20" 
                      : "text-[var(--color-anthracite-500)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]"
                  )}
                >
                  <item.icon className={clsx("w-5 h-5", isActive ? "text-white" : "text-[var(--color-anthracite-400)]")} />
                  {tAdmin(item.nameKey)}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Bottom Section */}
        <div className="mt-auto px-4 pb-4">
          <Link href="/notifications" className="block bg-[var(--bg-surface-hover)] rounded-xl border border-[var(--border-surface)] p-3 mb-4 flex items-center justify-between hover:border-[var(--color-lila-500)]/50 transition-colors">
            <div className="flex items-center gap-2">
              <div className="relative">
                <Bell className="w-5 h-5 text-[var(--color-anthracite-400)]" />
                {unreadCount > 0 && (
                  <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[var(--color-lila-500)] rounded-full border-2 border-[var(--bg-surface-hover)]"></div>
                )}
              </div>
              <div className="text-xs font-medium text-[var(--foreground)]">{tNav('notifications')} {unreadCount > 0 && `(${unreadCount})`}</div>
            </div>
          </Link>

          <div className="flex items-center justify-between text-xs text-[var(--color-anthracite-400)] px-2 mb-4">
            <span className="flex items-center gap-1.5"><kbd className="bg-[var(--bg-surface)] border border-[var(--border-surface)] px-1.5 rounded font-mono">⌘</kbd> + <kbd className="bg-[var(--bg-surface)] border border-[var(--border-surface)] px-1.5 rounded font-mono">K</kbd> for Ops</span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--border-surface)]">
          <div className="mb-4">
            <LanguageSwitcher />
          </div>
          <Link 
            href="/settings/profile"
            className="w-full flex items-center gap-3 px-3 py-2 mb-2 rounded-lg text-sm font-medium text-[var(--color-anthracite-400)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)] transition-colors"
            onClick={() => setIsMobileOpen(false)}
          >
            <Users className="w-5 h-5" />
            Profile Settings
          </Link>
          <button 
            onClick={() => signOut({ callbackUrl: '/login' })}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-semantic-error)] hover:bg-[var(--color-semantic-error)]/10 cursor-pointer transition-colors"
          >
            <LogOut className="w-5 h-5" />
            {tSidebar('sign_out')}
          </button>
        </div>
      </div>
    </>
  )
}
