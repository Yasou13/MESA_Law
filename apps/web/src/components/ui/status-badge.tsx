import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle2, Circle, CircleAlert, Clock3, type LucideIcon, ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"

export type StatusTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "review"
  | "verified"
  | "degraded"

export interface StatusBadgeProps {
  status: string
  label: string
  icon?: LucideIcon
  className?: string
}

const statusMap: Record<string, { classes: string; icon: LucideIcon }> = {
  neutral: { classes: "border-border bg-surface-subtle text-foreground-secondary", icon: Circle },
  success: { classes: "border-success/25 bg-success-soft text-success", icon: CheckCircle2 },
  approved: { classes: "border-success/25 bg-success-soft text-success", icon: CheckCircle2 },
  published: { classes: "border-success/25 bg-success-soft text-success", icon: CheckCircle2 },
  warning: { classes: "border-warning/25 bg-warning-soft text-warning", icon: AlertTriangle },
  error: { classes: "border-danger/25 bg-danger-soft text-danger", icon: CircleAlert },
  danger: { classes: "border-danger/25 bg-danger-soft text-danger", icon: CircleAlert },
  rejected: { classes: "border-danger/25 bg-danger-soft text-danger", icon: CircleAlert },
  conflict: { classes: "border-danger/25 bg-danger-soft text-danger", icon: CircleAlert },
  info: { classes: "border-info/25 bg-info-soft text-info", icon: Circle },
  processing: { classes: "border-info/25 bg-info-soft text-info", icon: Clock3 },
  running: { classes: "border-info/25 bg-info-soft text-info", icon: Clock3 },
  "review-required": { classes: "border-review/25 bg-review-soft text-review", icon: Clock3 },
  review: { classes: "border-review/25 bg-review-soft text-review", icon: Clock3 },
  proposed: { classes: "border-review/25 bg-review-soft text-review", icon: Clock3 },
  "manual-review": { classes: "border-review/25 bg-review-soft text-review", icon: Clock3 },
  verified: { classes: "border-verified/25 bg-verified-soft text-verified", icon: ShieldCheck },
  degraded: { classes: "border-warning/25 bg-warning-soft text-warning", icon: AlertTriangle },
  "stale-source": { classes: "border-warning/25 bg-warning-soft text-warning", icon: AlertTriangle },
  "legal-hold": { classes: "border-danger/25 bg-danger-soft text-danger", icon: CircleAlert },
}

export function StatusBadge({ status, label, icon: Icon, className }: StatusBadgeProps) {
  const config = statusMap[status.toLowerCase()] ?? statusMap.neutral
  const StatusIcon = Icon ?? config.icon

  return (
    <Badge
      className={cn(
        "flex h-6 items-center gap-1.5 rounded-full border px-2 text-xs font-medium",
        config.classes,
        className,
      )}
    >
      <StatusIcon className="size-3" aria-hidden="true" />
      {label}
    </Badge>
  )
}
