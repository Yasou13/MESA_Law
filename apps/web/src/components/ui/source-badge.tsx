"use client"

import { FileWarning, ShieldCheck } from 'lucide-react'
import { useTranslations } from 'next-intl'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export function SourceBadge({ lowProvenance, label, className }: {
  lowProvenance: boolean
  label?: string
  className?: string
}) {
  const t = useTranslations('Common')
  const Icon = lowProvenance ? FileWarning : ShieldCheck
  return (
    <Badge
      className={cn(
        'h-6 gap-1.5 rounded-full border px-2',
        lowProvenance
          ? 'border-warning/25 bg-warning-soft text-warning'
          : 'border-verified/25 bg-verified-soft text-verified',
        className,
      )}
    >
      <Icon className="size-3" aria-hidden="true" />
      {label ?? (lowProvenance ? t('lowProvenance') : t('verifiedSource'))}
    </Badge>
  )
}
