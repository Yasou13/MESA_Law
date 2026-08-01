'use client'

import * as React from 'react'
import {
  Settings,
  User,
  Search,
  Briefcase,
  FileStack,
  MessageSquareText,
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
import { useLocale } from 'next-intl'
import { localizedHref } from '@/lib/navigation'

export function CommandMenu() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()
  const locale = useLocale() as 'tr' | 'en'

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
        className="hidden h-8 w-full items-center gap-2 rounded-md border border-border bg-surface px-3 text-xs text-foreground-secondary shadow-xs transition-colors hover:bg-surface-subtle hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring md:flex"
        aria-label={locale === 'tr' ? 'Komut menüsünü aç' : 'Open command menu'}
      >
        <Search className="w-4 h-4" />
        <span className="flex-1 truncate text-left">{locale === 'tr' ? 'Dosya, belge veya komut ara' : 'Search matters, documents or commands'}</span>
        <kbd className="hidden items-center gap-1 rounded border border-border bg-surface-subtle px-1.5 py-0.5 font-mono text-[10px] sm:inline-flex">
          <span>⌘</span>K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder={locale === 'tr' ? 'Komut veya sayfa ara…' : 'Search commands or pages…'} />
        <CommandList>
          <CommandEmpty>{locale === 'tr' ? 'Sonuç bulunamadı.' : 'No results found.'}</CommandEmpty>
          
          <CommandGroup heading={locale === 'tr' ? 'Çalışma alanları' : 'Workspaces'}>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/matters')))}>
              <Briefcase className="mr-2 h-4 w-4" />
              <span>{locale === 'tr' ? 'Dosyalar' : 'Matters'}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/documents')))}>
              <FileStack className="mr-2 h-4 w-4" />
              <span>{locale === 'tr' ? 'Belgeler' : 'Documents'}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/ask-mesa')))}>
              <MessageSquareText className="mr-2 h-4 w-4" />
              <span>Ask MESA</span>
            </CommandItem>
          </CommandGroup>
          
          <CommandSeparator />
          
          <CommandGroup heading={locale === 'tr' ? 'Yönetim' : 'Administration'}>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/admin/members')))}>
              <User className="mr-2 h-4 w-4" />
              <span>{locale === 'tr' ? 'Firma üyeleri' : 'Firm members'}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/admin/settings')))}>
              <Settings className="mr-2 h-4 w-4" />
              <span>{locale === 'tr' ? 'Firma ayarları' : 'Firm settings'}</span>
              <CommandShortcut>⌘S</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
