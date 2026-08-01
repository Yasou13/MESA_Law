'use client'

import { Moon, Sun } from 'lucide-react'
import { useLocale } from 'next-intl'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const locale = useLocale()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  const isDark = mounted && resolvedTheme === 'dark'
  const label = locale === 'tr'
    ? (isDark ? 'Açık temaya geç' : 'Koyu temaya geç')
    : (isDark ? 'Switch to light theme' : 'Switch to dark theme')

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      aria-label={label}
      title={label}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
    </Button>
  )
}
