import { Gauge } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export function ConfidenceBadge({ value, label = 'Kaynak eşleşmesi', className }: {
  value: number | null
  label?: string
  className?: string
}) {
  const normalized = value == null ? null : Math.max(0, Math.min(1, value))
  const tone = normalized == null
    ? 'border-border bg-surface-subtle text-foreground-secondary'
    : normalized >= 0.8
      ? 'border-verified/25 bg-verified-soft text-verified'
      : normalized >= 0.5
        ? 'border-warning/25 bg-warning-soft text-warning'
        : 'border-danger/25 bg-danger-soft text-danger'
  return (
    <Badge className={cn('h-6 gap-1.5 rounded-full border px-2', tone, className)}>
      <Gauge className="size-3" aria-hidden="true" />
      {label}: {normalized == null ? 'sunulmadı' : `%${Math.round(normalized * 100)}`}
    </Badge>
  )
}
