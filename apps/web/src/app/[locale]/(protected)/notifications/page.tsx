'use client'

import { useListNotifications } from '@/api/endpoints/notifications/notifications'
import { Bell, Info, AlertCircle, CheckCircle, Check, Settings } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Button } from '@/components/ui/button'

export default function NotificationsPage() {
  const { data: notifications = [], isLoading } = useListNotifications()

  const getIcon = (category: string) => {
    switch (category) {
      case 'error': return <div className="w-10 h-10 rounded-full bg-[var(--color-semantic-error)]/10 flex items-center justify-center text-[var(--color-semantic-error)]"><AlertCircle className="w-5 h-5" /></div>
      case 'success': return <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500"><CheckCircle className="w-5 h-5" /></div>
      default: return <div className="w-10 h-10 rounded-full bg-[var(--color-lila-500)]/10 flex items-center justify-center text-[var(--color-lila-500)]"><Info className="w-5 h-5" /></div>
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center">
            <Bell className="w-5 h-5 text-[var(--color-lila-500)]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">Notifications</h1>
            <p className="text-[var(--color-anthracite-500)] mt-0.5">Your recent alerts and system updates.</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2 text-[var(--color-anthracite-400)]">
            <Check className="w-4 h-4" /> Mark All as Read
          </Button>
          <Button variant="ghost" size="icon-sm" className="text-[var(--color-anthracite-400)]">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-16 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
              <Bell className="w-8 h-8 text-[var(--color-anthracite-400)]" />
            </div>
            <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No notifications</h3>
            <p className="text-[var(--color-anthracite-400)] max-w-sm">
              You're all caught up! New alerts and updates will appear here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border-surface)]">
            {notifications.map((notif) => (
              <div key={notif.id} className="p-5 hover:bg-[var(--bg-surface-hover)] transition-colors flex gap-4 group">
                <div className="flex-shrink-0">
                  {getIcon(notif.category)}
                </div>
                <div className="flex-1 min-w-0 flex flex-col justify-center">
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="text-[15px] font-semibold text-[var(--foreground)] truncate">{notif.title}</h4>
                    <span className="text-xs font-medium text-[var(--color-anthracite-500)] whitespace-nowrap ml-4">
                      {formatDistanceToNow(new Date(notif.timestamp), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--color-anthracite-400)] leading-relaxed line-clamp-2">{notif.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
