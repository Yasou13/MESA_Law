'use client'

import { useGetNotificationsApiV1NotificationsGet } from '@/api/endpoints/notifications/notifications'
import { Bell, Info, AlertCircle, CheckCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function NotificationsPage() {
  const { data: res, isLoading } = useGetNotificationsApiV1NotificationsGet()
  const notifications: any[] = (res?.data as any) || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  const getIcon = (category: string) => {
    switch (category) {
      case 'error': return <AlertCircle className="w-5 h-5 text-red-400" />
      case 'success': return <CheckCircle className="w-5 h-5 text-green-400" />
      default: return <Info className="w-5 h-5 text-blue-400" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="w-6 h-6 text-[var(--color-lila-400)]" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-zinc-400">Your recent alerts and updates.</p>
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden divide-y divide-[var(--border-surface)]">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-zinc-400">
            No notifications available.
          </div>
        ) : (
          notifications.map((notif: any) => (
            <div key={notif.id} className="p-4 hover:bg-[var(--bg-surface-hover)] transition-colors flex gap-4">
              <div className="mt-1 flex-shrink-0">
                {getIcon(notif.category)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-semibold truncate">{notif.title}</h4>
                  <span className="text-xs text-zinc-500 whitespace-nowrap ml-4">
                    {formatDistanceToNow(new Date(notif.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <p className="text-sm text-zinc-400 mt-1">{notif.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
