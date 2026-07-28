'use client'
import { Activity, Clock, FileText, Bell, AlertTriangle } from 'lucide-react'
import Link from 'next/link'
import { useGetDashboardMetricsApiV1DashboardMetricsGet } from '@/api/endpoints/dashboard/dashboard'

export default function DashboardPage() {
  const { data: response, isLoading, isError, refetch } = useGetDashboardMetricsApiV1DashboardMetricsGet()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-lila-500)]"></div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Failed to load dashboard</h2>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-[var(--color-anthracite-700)] text-white rounded-lg hover:bg-[var(--color-anthracite-600)]"
        >
          Retry
        </button>
      </div>
    )
  }

  const metrics: any = response?.data || {}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-zinc-400">Welcome to MESA Law Intelligence Platform.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: 'Active Matters', value: metrics.active_matters, icon: <Activity className="w-5 h-5 text-blue-400" />, href: '/matters' },
          { title: 'Pending Reviews', value: metrics.pending_reviews, icon: <FileText className="w-5 h-5 text-purple-400" />, href: '/reviews' },
          { title: 'Upcoming Deadlines', value: metrics.upcoming_deadlines, icon: <Clock className="w-5 h-5 text-orange-400" />, href: '/deadlines' },
          { title: 'Unread Notifications', value: metrics.unread_notifications, icon: <Bell className="w-5 h-5 text-zinc-400" />, href: '/notifications' },
        ].map((stat, i) => (
          <Link key={i} href={stat.href}>
            <div className="glass-card rounded-xl p-6 transition-all hover:scale-[1.02] cursor-pointer h-full">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-zinc-400">{stat.title}</h3>
                {stat.icon}
              </div>
              <p className="text-3xl font-bold">{stat.value}</p>
            </div>
          </Link>
        ))}
      </div>
      
      {metrics.system_status === 'degraded' && (
        <div className="mt-6 p-4 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-start gap-4">
          <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-orange-400">System Capability Degraded</h4>
            <p className="text-sm text-orange-400/80 mt-1">
              Some intelligence features might be limited. Degraded components: {metrics.degraded_capabilities?.join(', ')}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
