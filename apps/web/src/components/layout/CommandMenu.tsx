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
import { useLocale, useTranslations } from 'next-intl'
import { localizedHref } from '@/lib/navigation'

export function CommandMenu() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()
  const locale = useLocale() as 'tr' | 'en'
  const t = useTranslations('Shell')
  const navigationT = useTranslations('Navigation')

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey)) {
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
        aria-label={t('openCommand')}
      >
        <Search className="w-4 h-4" />
        <span className="flex-1 truncate text-left">{t('commandSearch')}</span>
        <kbd className="hidden items-center gap-1 rounded border border-border bg-surface-subtle px-1.5 py-0.5 font-mono text-[10px] sm:inline-flex">
          <span>⌘</span>K
        </kbd>
      </button>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder={t('commandPlaceholder')} />
        <CommandList>
          <CommandEmpty>{t('noCommand')}</CommandEmpty>
          
          <CommandGroup heading={t('workspaces')}>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/matters')))}>
              <Briefcase className="mr-2 h-4 w-4" />
              <span>{navigationT('matters')}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/documents')))}>
              <FileStack className="mr-2 h-4 w-4" />
              <span>{navigationT('documents')}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/ask-mesa')))}>
              <MessageSquareText className="mr-2 h-4 w-4" />
              <span>Ask MESA</span>
            </CommandItem>
          </CommandGroup>
          
          <CommandSeparator />
          
          <CommandGroup heading={t('administration')}>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/admin/members')))}>
              <User className="mr-2 h-4 w-4" />
              <span>{t('firmMembers')}</span>
            </CommandItem>
            <CommandItem onSelect={() => runCommand(() => router.push(localizedHref(locale, '/admin/settings')))}>
              <Settings className="mr-2 h-4 w-4" />
              <span>{t('firmSettings')}</span>
              <CommandShortcut>⌘S</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
