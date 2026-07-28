'use client'

import * as React from 'react'
import {
  Settings,
  Smile,
  User,
  Search,
  FileText,
  Briefcase,
  ArrowRight,
} from 'lucide-react'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command'
import { useRouter } from 'next/navigation'

export function CommandMenu() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="hidden md:flex items-center gap-2 w-full max-w-sm px-4 py-2 text-sm text-[var(--color-anthracite-400)] bg-[var(--background)] border border-[var(--border-surface)] rounded-xl hover:bg-[var(--bg-surface-hover)] hover:text-[var(--foreground)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)]/50 focus:border-transparent"
      >
        <Search className="w-4 h-4" />
        <span className="flex-1 text-left">Search matters, documents, or queries...</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-[var(--bg-surface)] text-[var(--color-anthracite-400)] border border-[var(--border-surface)]">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Type a command or search..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          
          <CommandGroup heading="Quick Actions">
            <CommandItem onSelect={() => runCommand(() => router.push('/drafts'))}>
              <FileText className="mr-2 h-4 w-4" />
              <span>Create New Draft</span>
            </CommandItem>
          </CommandGroup>
          
          <CommandSeparator />
          
          <CommandGroup heading="Settings">
            <CommandItem onSelect={() => runCommand(() => router.push('/admin/members'))}>
              <User className="mr-2 h-4 w-4" />
              <span>Manage Firm Members</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push('/admin/settings'))}>
              <Settings className="mr-2 h-4 w-4" />
              <span>Firm Settings</span>
              <CommandShortcut>⌘S</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
