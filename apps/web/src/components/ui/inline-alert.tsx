import { AlertTriangle, CheckCircle2, CircleAlert, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type AlertTone = 'info' | 'success' | 'warning' | 'danger'

const tones = {
  info: { icon: Info, classes: 'border-info/25 bg-info-soft text-info' },
  success: { icon: CheckCircle2, classes: 'border-success/25 bg-success-soft text-success' },
  warning: { icon: AlertTriangle, classes: 'border-warning/25 bg-warning-soft text-warning' },
  danger: { icon: CircleAlert, classes: 'border-danger/25 bg-danger-soft text-danger' },
} satisfies Record<AlertTone, { icon: typeof Info; classes: string }>

function toneConfig(tone: AlertTone) {
  switch (tone) {
    case 'success': return tones.success
    case 'warning': return tones.warning
    case 'danger': return tones.danger
    default: return tones.info
  }
}

export function InlineAlert({
  tone = 'info',
  title,
  children,
  className,
}: {
  tone?: AlertTone
  title: string
  children?: ReactNode
  className?: string
}) {
  const { icon: Icon, classes } = toneConfig(tone)
  return (
    <div role={tone === 'danger' ? 'alert' : 'status'} className={cn('flex gap-3 rounded-lg border p-3.5', classes, className)}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        <p className="text-sm font-semibold">{title}</p>
        {children && <div className="mt-0.5 text-sm opacity-90">{children}</div>}
      </div>
    </div>
  )
}
