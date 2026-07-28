'use client'
import { Activity, Clock, FileText, Bell, AlertTriangle, ArrowRight, FolderOpen } from 'lucide-react'
import Link from 'next/link'
import { useGetDashboardMetricsApiV1DashboardMetricsGet } from '@/api/endpoints/dashboard/dashboard'
import { useListMatters } from '@/api/endpoints/default/default'
import { useListDeadlines } from '@/api/endpoints/deadlines/deadlines'
import { useListDraftReviewsApiV1ReviewsGet } from '@/api/endpoints/reviews/reviews'
import { StatusBadge } from '@/components/ui/status-badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  const { data: response, isLoading: isLoadingMetrics, isError, refetch } = useGetDashboardMetricsApiV1DashboardMetricsGet()
  const { data: mattersRes, isLoading: isLoadingMatters } = useListMatters()
  const { data: deadlinesRes, isLoading: isLoadingDeadlines } = useListDeadlines()
  const { data: reviewsRes, isLoading: isLoadingReviews } = useListDraftReviewsApiV1ReviewsGet()

  if (isLoadingMetrics) {
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
        <Button onClick={() => refetch()} variant="outline">Retry</Button>
      </div>
    )
  }

  const metrics: any = response?.data || {}
  const recentMatters: any[] = ((mattersRes?.data as any)?.items || (mattersRes?.data as any) || []).slice(0, 5)
  const upcomingDeadlines: any[] = ((deadlinesRes?.data as any)?.items || (deadlinesRes?.data as any) || []).slice(0, 5)
  const pendingReviews: any[] = ((reviewsRes?.data as any) || []).slice(0, 5)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-zinc-500 dark:text-zinc-400">Welcome to MESA Law Intelligence Platform.</p>
      </div>
      
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: 'Active Matters', value: metrics.active_matters, icon: <Activity className="w-5 h-5 text-blue-400" />, href: '/matters' },
          { title: 'Pending Reviews', value: metrics.pending_reviews, icon: <FileText className="w-5 h-5 text-purple-400" />, href: '/reviews' },
          { title: 'Upcoming Deadlines', value: metrics.upcoming_deadlines, icon: <Clock className="w-5 h-5 text-orange-400" />, href: '/deadlines' },
          { title: 'Unread Notifications', value: metrics.unread_notifications, icon: <Bell className="w-5 h-5 text-zinc-400" />, href: '/notifications' },
        ].map((stat, i) => (
          <Link key={i} href={stat.href} className="block">
            <div className="glass-card rounded-xl p-6 transition-all hover:scale-[1.02] h-full flex flex-col justify-between group">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400 group-hover:text-[var(--foreground)] transition-colors">{stat.title}</h3>
                {stat.icon}
              </div>
              <p className="text-3xl font-bold">{stat.value}</p>
            </div>
          </Link>
        ))}
      </div>
      
      {metrics.system_status === 'degraded' && (
        <div className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-start gap-4">
          <AlertTriangle className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-orange-600 dark:text-orange-400">System Capability Degraded</h4>
            <p className="text-sm text-orange-600/80 dark:text-orange-400/80 mt-1">
              Some intelligence features might be limited. Degraded components: {metrics.degraded_capabilities?.join(', ')}
            </p>
          </div>
        </div>
      )}

      {/* Widgets Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Matters Widget */}
        <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
          <div className="p-4 border-b border-[var(--border-surface)] flex items-center justify-between bg-[var(--bg-surface)]">
            <h3 className="font-semibold flex items-center gap-2"><FolderOpen className="w-4 h-4 text-[var(--color-anthracite-500)]" /> Active Matters</h3>
            <Link href="/matters" className="text-xs text-[var(--color-lila-600)] hover:underline flex items-center gap-1">View all <ArrowRight className="w-3 h-3" /></Link>
          </div>
          <div className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Matter Name</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoadingMatters ? (
                  <TableRow><TableCell colSpan={2} className="text-center py-4">Loading...</TableCell></TableRow>
                ) : recentMatters.length === 0 ? (
                  <TableRow><TableCell colSpan={2} className="text-center py-4 text-zinc-400">No active matters</TableCell></TableRow>
                ) : (
                  recentMatters.map(m => (
                    <TableRow key={m.id}>
                      <TableCell className="font-medium">
                        <Link href={`/matters/${m.id}`} className="hover:underline">{m.name}</Link>
                      </TableCell>
                      <TableCell><StatusBadge status={m.status === 'open' ? 'success' : 'neutral'} label={m.status.toUpperCase()} /></TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Upcoming Deadlines Widget */}
        <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
          <div className="p-4 border-b border-[var(--border-surface)] flex items-center justify-between bg-[var(--bg-surface)]">
            <h3 className="font-semibold flex items-center gap-2"><Clock className="w-4 h-4 text-orange-500" /> Upcoming Deadlines</h3>
            <Link href="/deadlines" className="text-xs text-[var(--color-lila-600)] hover:underline flex items-center gap-1">View all <ArrowRight className="w-3 h-3" /></Link>
          </div>
          <div className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Due Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoadingDeadlines ? (
                  <TableRow><TableCell colSpan={2} className="text-center py-4">Loading...</TableCell></TableRow>
                ) : upcomingDeadlines.length === 0 ? (
                  <TableRow><TableCell colSpan={2} className="text-center py-4 text-zinc-400">No upcoming deadlines</TableCell></TableRow>
                ) : (
                  upcomingDeadlines.map(d => (
                    <TableRow key={d.id}>
                      <TableCell className="font-medium">{d.description}</TableCell>
                      <TableCell className="text-orange-500">{new Date(d.due_date).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
        
        {/* Pending Reviews Widget */}
        <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden lg:col-span-2">
          <div className="p-4 border-b border-[var(--border-surface)] flex items-center justify-between bg-[var(--bg-surface)]">
            <h3 className="font-semibold flex items-center gap-2"><FileText className="w-4 h-4 text-purple-500" /> Pending Reviews</h3>
            <Link href="/reviews" className="text-xs text-[var(--color-lila-600)] hover:underline flex items-center gap-1">View all <ArrowRight className="w-3 h-3" /></Link>
          </div>
          <div className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Review Type</TableHead>
                  <TableHead>Target ID</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoadingReviews ? (
                  <TableRow><TableCell colSpan={3} className="text-center py-4">Loading...</TableCell></TableRow>
                ) : pendingReviews.length === 0 ? (
                  <TableRow><TableCell colSpan={3} className="text-center py-4 text-zinc-400">No pending reviews</TableCell></TableRow>
                ) : (
                  pendingReviews.map((r: any) => (
                    <TableRow key={r.id}>
                      <TableCell className="font-medium capitalize">{r.review_type}</TableCell>
                      <TableCell className="text-zinc-500 text-sm font-mono">{r.target_id}</TableCell>
                      <TableCell><StatusBadge status="review-required" label={r.status} /></TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  )
}
