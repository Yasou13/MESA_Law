import { Badge } from "@/components/ui/badge"
import { LucideIcon } from "lucide-react"

export interface StatusBadgeProps {
  status: string
  label: string
  icon?: LucideIcon
  className?: string
}

const statusMap: Record<string, string> = {
  success: "bg-[var(--color-semantic-success)] text-white hover:bg-[var(--color-semantic-success)]/90",
  warning: "bg-[var(--color-semantic-warning)] text-white hover:bg-[var(--color-semantic-warning)]/90",
  error: "bg-[var(--color-semantic-error)] text-white hover:bg-[var(--color-semantic-error)]/90",
  info: "bg-[var(--color-semantic-info)] text-white hover:bg-[var(--color-semantic-info)]/90",
  processing: "bg-[var(--color-semantic-processing)] text-white hover:bg-[var(--color-semantic-processing)]/90",
  "review-required": "bg-[var(--color-semantic-review-required)] text-white hover:bg-[var(--color-semantic-review-required)]/90",
  "stale-source": "bg-[var(--color-semantic-stale-source)] text-white hover:bg-[var(--color-semantic-stale-source)]/90",
  "legal-hold": "bg-[var(--color-semantic-legal-hold)] text-white hover:bg-[var(--color-semantic-legal-hold)]/90",
  degraded: "bg-[var(--color-semantic-degraded)] text-white hover:bg-[var(--color-semantic-degraded)]/90",
  "manual-review": "bg-[var(--color-semantic-manual-review)] text-white hover:bg-[var(--color-semantic-manual-review)]/90",
  conflict: "bg-[var(--color-semantic-conflict)] text-white hover:bg-[var(--color-semantic-conflict)]/90",
}

export function StatusBadge({ status, label, icon: Icon, className }: StatusBadgeProps) {
  const statusClasses = statusMap[status.toLowerCase()] || "bg-[var(--color-semantic-neutral)] text-white hover:bg-[var(--color-semantic-neutral)]/90"

  return (
    <Badge className={`${statusClasses} flex items-center gap-1.5 px-2 py-0.5 rounded-full font-medium ${className || ''}`}>
      {Icon && <Icon className="w-3.5 h-3.5" />}
      {label}
    </Badge>
  )
}
