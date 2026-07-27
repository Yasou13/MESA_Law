'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FolderOpen, Search, LogOut, CheckSquare } from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Matters', href: '/matters', icon: FolderOpen },
  { name: 'QA Review', href: '/qa', icon: CheckSquare },
  { name: 'Research', href: '/research', icon: Search },
]

export function Sidebar() {
  const pathname = usePathname()
  
  if (pathname === '/login') return null

  return (
    <div className="flex flex-col w-64 border-r border-white/10 bg-black/40 backdrop-blur-xl h-screen sticky top-0">
      <div className="p-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-xl">
            M
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            MESA Law
          </span>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-blue-600/10 text-blue-400 border border-blue-500/20" 
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5 border border-transparent"
              )}
            >
              <item.icon className={clsx("w-5 h-5", isActive ? "text-blue-400" : "text-zinc-500")} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-3 py-2 text-sm text-zinc-400 hover:text-zinc-100 cursor-pointer transition-colors">
          <LogOut className="w-5 h-5" />
          Sign out
        </div>
      </div>
    </div>
  )
}
