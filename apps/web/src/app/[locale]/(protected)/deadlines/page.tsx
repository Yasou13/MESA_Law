'use client'

import { useListDeadlines, useCompleteDeadline } from '@/api/endpoints/deadlines/deadlines'
import { Clock, CheckCircle, AlertCircle, Calendar } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { useQueryClient } from '@tanstack/react-query'

export default function DeadlinesPage() {
  const queryClient = useQueryClient()
  const { data: res, isLoading, isError, refetch } = useListDeadlines()
  const { mutate: completeMutate, isPending } = useCompleteDeadline()

  const deadlines = (res as unknown as any[]) || []

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
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Failed to load deadlines</h2>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-[var(--color-anthracite-700)] text-white rounded-lg hover:bg-[var(--color-anthracite-600)]"
        >
          Retry
        </button>
      </div>
    )
  }

  const handleComplete = (id: string) => {
    completeMutate({ deadlineId: id }, {
      onSuccess: () => {
        toast.success('Deadline marked as completed')
        queryClient.invalidateQueries({ queryKey: ['/api/v1/deadlines'] })
      },
      onError: (err: any) => {
        toast.error(`Failed to complete: ${err.response?.data?.detail || 'Unknown error'}`)
      }
    })
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Deadlines</h1>
          <p className="text-zinc-400">Track and manage upcoming deadlines across all your matters.</p>
        </div>
      </div>

      <div className="space-y-4">
        {deadlines.length === 0 ? (
          <div className="glass-card rounded-xl p-12 text-center text-zinc-400">
            <CheckCircle className="w-12 h-12 text-green-400/50 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--foreground)] mb-1">No pending deadlines</h3>
            <p>You&apos;re all caught up on your deadlines.</p>
          </div>
        ) : (
          deadlines.map((deadline: any) => {
            const isOverdue = new Date(deadline.due_date) < new Date()
            return (
              <div key={deadline.id} className="glass-card rounded-xl p-6 flex items-center justify-between transition-all hover:border-[var(--color-lila-500)]/30">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${isOverdue ? 'bg-red-500/10 border-red-500/20 text-red-500' : 'bg-orange-500/10 border-orange-500/20 text-orange-400'}`}>
                    <Calendar className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{deadline.description}</h3>
                    <div className="flex flex-col gap-1 mt-1 text-sm text-zinc-400">
                      <span className="flex items-center gap-1 font-mono">
                        Matter: <span className="text-[var(--color-lila-400)]">{deadline.matter_id}</span>
                      </span>
                      <span className={`flex items-center gap-1 font-medium ${isOverdue ? 'text-red-400' : 'text-orange-400'}`}>
                        <Clock className="w-3 h-3" /> Due: {new Date(deadline.due_date).toLocaleDateString()}
                        {isOverdue && ' (OVERDUE)'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <button 
                    onClick={() => handleComplete(deadline.id)}
                    disabled={isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-500 hover:bg-green-500/20 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" /> Mark Complete
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
