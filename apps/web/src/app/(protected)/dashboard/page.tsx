'use client'
import { Activity, Clock, FileText, Bell } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-zinc-400">Welcome to MESA Law Intelligence Platform.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: 'Active Matters', value: '12', icon: <Activity className="w-5 h-5 text-blue-400" /> },
          { title: 'Pending Reviews', value: '5', icon: <FileText className="w-5 h-5 text-purple-400" /> },
          { title: 'Upcoming Deadlines', value: '3', icon: <Clock className="w-5 h-5 text-orange-400" /> },
          { title: 'Unread Notifications', value: '2', icon: <Bell className="w-5 h-5 text-zinc-400" /> },
        ].map((stat, i) => (
          <div key={i} className="glass-card rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-zinc-400">{stat.title}</h3>
              {stat.icon}
            </div>
            <p className="text-3xl font-bold">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
