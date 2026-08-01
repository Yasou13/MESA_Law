'use client'

import {
  BookOpenCheck,
  BriefcaseBusiness,
  FileStack,
  Gauge,
  MessageSquareText,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react'
import Link from 'next/link'
import { useLocale, useTranslations } from 'next-intl'
import { usePathname } from 'next/navigation'
import { useEffect, useRef } from 'react'

import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { localizedHref, pathnameWithoutLocale } from '@/lib/navigation'

const navigation = [
  { key: 'dashboard', href: '/dashboard', icon: Gauge },
  { key: 'matters', href: '/matters', icon: BriefcaseBusiness },
  { key: 'documents', href: '/documents', icon: FileStack },
  { key: 'review_center', href: '/reviews', icon: BookOpenCheck },
  { key: 'askMesa', href: '/ask-mesa', icon: MessageSquareText },
  { key: 'operations', href: '/operations', icon: ShieldCheck },
  { key: 'settings', href: '/settings/profile', icon: Settings },
] as const

interface SidebarProps {
  mobileOpen: boolean
  onMobileClose: () => void
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname()
  const locale = useLocale() as 'tr' | 'en'
  const navigationT = useTranslations('Navigation')
  const sidebarT = useTranslations('Sidebar')
  const routePath = pathnameWithoutLocale(pathname)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const mobileDialogRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!mobileOpen) return
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()
    const handleDialogKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onMobileClose()
        return
      }
      if (event.key !== 'Tab') return
      const focusable = Array.from(
        mobileDialogRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      ).filter((element) => element.offsetParent !== null)
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleDialogKey)
    return () => {
      document.removeEventListener('keydown', handleDialogKey)
      document.body.style.overflow = previousOverflow
      previousFocus?.focus()
    }
  }, [mobileOpen, onMobileClose])

  const content = (
    <>
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-sidebar-border px-4 lg:justify-center xl:justify-start">
        <Link
          href={localizedHref(locale, '/dashboard')}
          onClick={onMobileClose}
          className="flex min-w-0 items-center gap-3 rounded-md focus-visible:outline-offset-4"
        >
          {/* The existing product mark is intentionally preserved. */}
          <img src="/icon-192.png" alt="MESA" className="size-8 rounded-md" />
          <span className="truncate text-base font-semibold tracking-[-0.01em] text-white lg:hidden xl:inline">
            MESA Law
          </span>
        </Link>
        <button
          ref={closeButtonRef}
          type="button"
          onClick={onMobileClose}
          className="flex size-10 items-center justify-center rounded-md text-sidebar-foreground hover:bg-sidebar-accent hover:text-white lg:hidden"
          aria-label={sidebarT('close')}
        >
          <X className="size-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5" aria-label={sidebarT('mainNavigation')}>
        {navigation.map((item) => {
          const active = item.href === '/dashboard'
            ? routePath === item.href
            : routePath.startsWith(item.href)
          const link = (
            <Link
              key={item.href}
              href={localizedHref(locale, item.href)}
              onClick={onMobileClose}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group relative flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors duration-150',
                active
                  ? 'bg-sidebar-accent text-white before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:rounded-full before:bg-primary-100'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-white',
                'lg:justify-center lg:px-0 xl:justify-start xl:px-3',
              )}
            >
              <item.icon className="size-[18px] shrink-0" strokeWidth={1.8} aria-hidden="true" />
              <span className="truncate lg:hidden xl:inline">{navigationT(item.key)}</span>
            </Link>
          )
          return (
            <Tooltip key={item.href}>
              <TooltipTrigger render={link} />
              <TooltipContent side="right" className="hidden lg:block xl:hidden">{navigationT(item.key)}</TooltipContent>
            </Tooltip>
          )
        })}
      </nav>

      <div className="border-t border-sidebar-border px-4 py-4 text-xs leading-5 text-sidebar-foreground lg:hidden xl:block">
        <p className="font-medium text-white">MESA Law</p>
        <p>{sidebarT('tagline')}</p>
      </div>
    </>
  )

  return (
    <>
      <aside data-testid="desktop-sidebar" className="hidden h-screen w-[72px] shrink-0 flex-col bg-sidebar lg:flex xl:w-64">
        {content}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label={sidebarT('close')}
            className="absolute inset-0 bg-neutral-950/50"
            onClick={onMobileClose}
          />
          <aside
            ref={mobileDialogRef}
            data-testid="mobile-navigation"
            role="dialog"
            aria-modal="true"
            aria-label={sidebarT('mainNavigation')}
            className="relative flex h-full w-[min(20rem,88vw)] flex-col bg-sidebar shadow-md"
          >
            {content}
          </aside>
        </div>
      )}
    </>
  )
}
