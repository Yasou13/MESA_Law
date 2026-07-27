'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FolderOpen, Search, LogOut, CheckSquare, LayoutDashboard, Settings, Users, Bell } from 'lucide-react'
import { clsx } from 'clsx'
import { signOut } from 'next-auth/react'
import { OperationsMenu } from './OperationsMenu'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Matters', href: '/matters', icon: FolderOpen },
  { name: 'QA Review', href: '/qa', icon: CheckSquare },
  { name: 'Research', href: '/research', icon: Search },
]

const adminNavigation = [
  { name: 'Members', href: '/admin/members', icon: Users },
  { name: 'Settings', href: '/admin/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 border-r border-[var(--border-surface)] bg-[var(--bg-surface)] backdrop-blur-xl h-screen sticky top-0">
      <div className="p-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--color-lila-600)] flex items-center justify-center font-bold text-white text-xl shadow-lg">
            M
          </div>
          <span className="text-xl font-bold text-[var(--foreground)]">
            MESA Law
          </span>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-[var(--color-lila-500)] text-white shadow-md shadow-[var(--color-lila-500)]/20" 
                  : "text-[var(--color-anthracite-500)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]"
              )}
            >
              <item.icon className={clsx("w-5 h-5", isActive ? "text-white" : "text-[var(--color-anthracite-400)]")} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="mt-8 px-4">
        <h3 className="px-3 text-xs font-semibold text-[var(--color-anthracite-400)] uppercase tracking-wider mb-2">Administration</h3>
        <nav className="space-y-1">
          {adminNavigation.map((item) => {
            const isActive = pathname.startsWith(item.href)
            return (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-[var(--color-lila-500)] text-white shadow-md shadow-[var(--color-lila-500)]/20" 
                    : "text-[var(--color-anthracite-500)] hover:text-[var(--foreground)] hover:bg-[var(--bg-surface-hover)]"
                )}
              >
                <item.icon className={clsx("w-5 h-5", isActive ? "text-white" : "text-[var(--color-anthracite-400)]")} />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="mt-auto px-4 pb-4">
        <div className="bg-[var(--bg-surface-hover)] rounded-xl border border-[var(--border-surface)] p-3 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Bell className="w-5 h-5 text-[var(--color-anthracite-400)]" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[var(--color-lila-500)] rounded-full border-2 border-[var(--bg-surface-hover)]"></div>
            </div>
            <div className="text-xs font-medium text-[var(--foreground)]">3 Notifications</div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-[var(--color-anthracite-400)] px-2 mb-4">
          <span className="flex items-center gap-1.5"><kbd className="bg-[var(--bg-surface)] border border-[var(--border-surface)] px-1.5 rounded font-mono">⌘</kbd> + <kbd className="bg-[var(--bg-surface)] border border-[var(--border-surface)] px-1.5 rounded font-mono">K</kbd> for Ops</span>
        </div>
      </div>

      <div className="p-4 border-t border-[var(--border-surface)]">
        <button 
          onClick={() => signOut({ callbackUrl: '/login' })}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-[var(--color-semantic-error)] hover:bg-[var(--color-semantic-error)]/10 cursor-pointer transition-colors"
        >
          <LogOut className="w-5 h-5" />
          Sign out
        </button>
      </div>
      <OperationsMenu />
    </div>
  )
}
