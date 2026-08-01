'use client'

import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useState } from 'react'
import { Plus, FolderOpen, Loader2, Search, ArrowRight, Clock, LayoutGrid, List } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx } from 'clsx'
import {
  getListMattersQueryKey,
  useConflictCheck,
  useCreateMatter,
  useListMatters,
  useOverrideConflict,
} from '@/api/endpoints/default/default'
import type { ConflictResult, MatterResponse } from '@/api/models'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/ui/status-badge'

const matterSchema = z.object({
  title: z.string().min(3, 'Matter name must be at least 3 characters'),
  description: z.string().optional(),
  partyNames: z.string().min(1, 'Please enter at least one party name for conflict checking'),
})

type MatterFormValues = z.infer<typeof matterSchema>

export default function MattersPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState<'card' | 'table'>('card')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [conflicts, setConflicts] = useState<ConflictResult[] | null>(null)
  const [overrideReason, setOverrideReason] = useState('')

  const { data: allMatters = [], isLoading } = useListMatters()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<MatterFormValues>({
    resolver: zodResolver(matterSchema),
    defaultValues: { title: '', description: '', partyNames: '' }
  })

  const conflictCheck = useConflictCheck()
  const createMatter = useCreateMatter()
  const overrideConflict = useOverrideConflict()

  const finishCreation = () => {
    queryClient.invalidateQueries({ queryKey: getListMattersQueryKey() })
    reset()
    setIsCreateOpen(false)
    setConflicts(null)
    setOverrideReason('')
  }

  const createWorkspace = async (data: MatterFormValues, reason?: string) => {
    let createdMatter: MatterResponse | undefined
    try {
      createdMatter = await createMatter.mutateAsync({ data: { title: data.title } })
      if (reason) {
        await overrideConflict.mutateAsync({
          matterId: createdMatter.id,
          data: { reason },
        })
      }
      finishCreation()
      toast.success(
        reason
          ? 'Matter created and conflict override recorded'
          : 'Matter workspace created successfully',
      )
    } catch {
      if (createdMatter) {
        finishCreation()
        toast.error(
          'Matter was created, but the conflict override audit failed. Contact an administrator before using it.',
        )
        return
      }
      toast.error('Failed to create workspace')
    }
  }

  const onSubmit = async (data: MatterFormValues) => {
    if (conflicts !== null) {
      const reason = overrideReason.trim()
      if (reason.length < 3) {
        toast.error('A conflict override reason of at least 3 characters is required')
        return
      }
      await createWorkspace(data, reason)
      return
    }
    
    // First run conflict check
    const parties = data.partyNames.split(',').map(p => p.trim()).filter(Boolean)
    conflictCheck.mutate({ data: { party_names: parties } }, {
      onSuccess: (res) => {
        if (res.has_conflicts) {
          setConflicts(res.conflicts)
          toast.error('Conflicts found! Please review.')
        } else {
          void createWorkspace(data)
        }
      },
      onError: () => {
        toast.error('Failed to run conflict check')
      }
    })
  }

  const filteredMatters = allMatters.filter((matter) =>
    matter.title.toLowerCase().includes(search.toLowerCase()),
  )

  const getMattersByStatus = (statusGroup: string) => {
    if (statusGroup === 'active') return filteredMatters.filter(m => m.status?.toLowerCase() === 'open' || m.status === 'ACTIVE')
    if (statusGroup === 'pending') return filteredMatters.filter(m => m.status?.toLowerCase() === 'pending')
    if (statusGroup === 'closed') return filteredMatters.filter(m => m.status?.toLowerCase() === 'closed')
    return filteredMatters
  }

  const renderCardView = (mattersList: MatterResponse[]) => {
    if (mattersList.length === 0) return <EmptyState />
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        {mattersList.map((matter, i) => (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            key={matter.id}
          >
            <Link 
              href={`/matters/${matter.id}`}
              className="block p-6 glass-card rounded-2xl hover:border-[var(--color-lila-500)]/30 transition-all duration-300 group relative overflow-hidden h-full"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-lila-500)]/5 to-[var(--color-anthracite-500)]/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="w-12 h-12 rounded-xl bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <FolderOpen className="w-6 h-6 text-[var(--color-lila-600)] dark:text-[var(--color-lila-500)]" />
                </div>
                <StatusBadge status={matter.status === 'open' ? 'success' : 'neutral'} label={(matter.status || 'ACTIVE').toUpperCase()} />
              </div>
              
              <h3 className="text-xl font-bold text-[var(--foreground)] group-hover:text-[var(--color-lila-600)] dark:group-hover:text-[var(--color-lila-500)] transition-colors relative z-10 mb-2 truncate">
                {matter.title}
              </h3>
              
              <div className="flex items-center gap-4 mt-6 text-sm text-[var(--color-anthracite-400)] relative z-10">
                <span>{matter.client_name ?? 'Client not specified'}</span>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
                  <span className="font-mono">{matter.id.substring(0, 6)}</span>
                </div>
              </div>

              <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all text-[var(--color-lila-600)] dark:text-[var(--color-lila-500)]">
                <ArrowRight className="w-5 h-5" />
              </div>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    )
  }

  const renderTableView = (mattersList: MatterResponse[]) => {
    if (mattersList.length === 0) return <EmptyState />
    return (
      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Matter Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Reference ID</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mattersList.map(m => (
              <TableRow key={m.id}>
                <TableCell className="font-medium">
                  <Link href={`/matters/${m.id}`} className="hover:underline flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-[var(--color-anthracite-400)]" />
                    {m.title}
                  </Link>
                </TableCell>
                <TableCell><StatusBadge status={m.status === 'open' ? 'success' : 'neutral'} label={(m.status || 'ACTIVE').toUpperCase()} /></TableCell>
                <TableCell className="font-mono text-sm text-[var(--color-anthracite-500)]">{m.id.substring(0, 8)}</TableCell>
                <TableCell className="text-right">
                  <Link href={`/matters/${m.id}`} className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
                    Open
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    )
  }

  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-24 glass-card rounded-3xl border-dashed border-2 border-[var(--border-surface)]">
      <div className="w-16 h-16 rounded-full bg-[var(--bg-surface-hover)] flex items-center justify-center mb-4">
        <FolderOpen className="w-8 h-8 text-[var(--color-anthracite-400)]" />
      </div>
      <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No workspaces found</h3>
      <p className="text-[var(--color-anthracite-500)] text-center max-w-sm">
        No matters match your current filters. Get started by creating a new one.
      </p>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)] mb-2">Matter Workspaces</h1>
          <p className="text-[var(--color-anthracite-500)]">Manage matter-scoped documents, reviews, publication and sourced Q&amp;A.</p>
        </div>
        
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger render={<Button className="gap-2" size="lg" />}>
            <Plus className="w-4 h-4" /> New Matter
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <form onSubmit={handleSubmit(onSubmit)}>
              <DialogHeader>
                <DialogTitle>Create New Matter</DialogTitle>
                <DialogDescription>
                  Initialize a matter workspace. A MESA Core binding is configured separately after creation.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-6">
                {!conflicts ? (
                  <>
                    <div className="space-y-2">
                      <label htmlFor="title" className="text-sm font-medium">Matter Name</label>
                      <Input id="title" placeholder="e.g. Acme Corp Acquisition" {...register('title')} />
                      {errors.title && <p className="text-sm text-[var(--color-semantic-error)]">{errors.title.message}</p>}
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="partyNames" className="text-sm font-medium">Parties (comma separated)</label>
                      <Input id="partyNames" placeholder="e.g. Acme Corp, Globex" {...register('partyNames')} />
                      {errors.partyNames && <p className="text-sm text-[var(--color-semantic-error)]">{errors.partyNames.message}</p>}
                    </div>
                  </>
                ) : (
                  <div className="space-y-4">
                    <div className="p-4 bg-[var(--color-semantic-error)]/10 text-[var(--color-semantic-error)] rounded-lg border border-[var(--color-semantic-error)]/20">
                      <h4 className="font-bold mb-2">Potential Conflicts Detected</h4>
                      <ul className="list-disc pl-4 text-sm space-y-1">
                        {conflicts.map((c, i) => (
                          <li key={i}>
                            <strong>{c.matched_name}</strong> in matter <em>{c.matter_title}</em> (Role: {c.role})
                          </li>
                        ))}
                      </ul>
                    </div>
                    <p className="text-sm text-[var(--color-anthracite-400)]">
                      Do you want to override these conflicts and create the matter anyway?
                    </p>
                    <div className="space-y-2">
                      <label htmlFor="overrideReason" className="text-sm font-medium">
                        Override reason
                      </label>
                      <Input
                        id="overrideReason"
                        value={overrideReason}
                        onChange={(event) => setOverrideReason(event.target.value)}
                        placeholder="Document the business and ethical basis"
                        minLength={3}
                        required
                      />
                      <p className="text-xs text-[var(--color-anthracite-400)]">
                        This reason is written to the audit log.
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => {
                  if (conflicts) {
                    setConflicts(null)
                    setOverrideReason('')
                  } else {
                    setIsCreateOpen(false)
                  }
                }}>
                  {conflicts ? 'Back' : 'Cancel'}
                </Button>
                <Button
                  type="submit"
                  disabled={
                    createMatter.isPending ||
                    conflictCheck.isPending ||
                    overrideConflict.isPending
                  }
                >
                  {createMatter.isPending || conflictCheck.isPending || overrideConflict.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  {conflicts ? 'Override & Create' : 'Check Conflicts & Create'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-anthracite-400)]" />
          <Input 
            type="text" 
            placeholder="Search matters by name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 w-full"
          />
        </div>
        
        <div className="flex items-center gap-2 bg-[var(--bg-surface-hover)] p-1 rounded-lg border border-[var(--border-surface)] self-end">
          <button 
            onClick={() => setViewMode('card')}
            className={clsx("p-1.5 rounded-md transition-colors", viewMode === 'card' ? "bg-[var(--bg-surface)] shadow-sm text-[var(--foreground)]" : "text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]")}
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button 
            onClick={() => setViewMode('table')}
            className={clsx("p-1.5 rounded-md transition-colors", viewMode === 'table' ? "bg-[var(--bg-surface)] shadow-sm text-[var(--foreground)]" : "text-[var(--color-anthracite-400)] hover:text-[var(--foreground)]")}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--color-lila-500)]" />
          <p className="text-[var(--color-anthracite-500)] animate-pulse">Loading workspaces...</p>
        </div>
      ) : (
        <Tabs defaultValue="active" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="closed">Closed</TabsTrigger>
            <TabsTrigger value="all">All Matters</TabsTrigger>
          </TabsList>
          
          <TabsContent value="active" className="mt-0">
            {viewMode === 'card' ? renderCardView(getMattersByStatus('active')) : renderTableView(getMattersByStatus('active'))}
          </TabsContent>
          <TabsContent value="pending" className="mt-0">
            {viewMode === 'card' ? renderCardView(getMattersByStatus('pending')) : renderTableView(getMattersByStatus('pending'))}
          </TabsContent>
          <TabsContent value="closed" className="mt-0">
            {viewMode === 'card' ? renderCardView(getMattersByStatus('closed')) : renderTableView(getMattersByStatus('closed'))}
          </TabsContent>
          <TabsContent value="all" className="mt-0">
            {viewMode === 'card' ? renderCardView(filteredMatters) : renderTableView(filteredMatters)}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
