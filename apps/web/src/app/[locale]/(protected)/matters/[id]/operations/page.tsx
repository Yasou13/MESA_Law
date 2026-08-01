'use client'

import { useLocale } from 'next-intl'
import { use } from 'react'

import { useListJobs } from '@/api/endpoints/operations/operations'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { PageHeader } from '@/components/ui/page-header'
import { Panel } from '@/components/ui/panel'
import { StatusBadge } from '@/components/ui/status-badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export default function MatterOperationsPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const locale = useLocale()
  const { data: jobs = [], isLoading, isError, refetch } = useListJobs({ limit: 100 })
  const matterJobs = jobs.filter((job) => job.matter_id === matterId)

  return (
    <div className="space-y-5">
      <PageHeader title={locale === 'tr' ? 'Dosya operasyonları' : 'Matter operations'} description={locale === 'tr' ? 'Belge işleme ve MESA yayın kuyruğunun bu dosyaya ait görünümü.' : 'Matter-scoped document processing and MESA publication queue.'} />
      {isLoading ? <LoadingState /> : isError ? (
        <ErrorState title={locale === 'tr' ? 'Operasyonlar yüklenemedi' : 'Operations could not be loaded'} description={locale === 'tr' ? 'Arka plan işleri çalışmaya devam edebilir; yeniden deneyin.' : 'Background work may continue; try again.'} onRetry={() => refetch()} />
      ) : matterJobs.length === 0 ? (
        <NoDataState title={locale === 'tr' ? 'Operasyon bulunmuyor' : 'No operations found'} description={locale === 'tr' ? 'Bu dosya için henüz arka plan işi oluşturulmadı.' : 'No background job has been created for this matter.'} />
      ) : (
        <Panel className="overflow-hidden"><Table><TableHeader><TableRow><TableHead>{locale === 'tr' ? 'İşlem' : 'Operation'}</TableHead><TableHead>{locale === 'tr' ? 'Durum' : 'Status'}</TableHead><TableHead>{locale === 'tr' ? 'Deneme' : 'Attempts'}</TableHead><TableHead>{locale === 'tr' ? 'Güncelleme' : 'Updated'}</TableHead><TableHead>Correlation ID</TableHead></TableRow></TableHeader><TableBody>{matterJobs.map((job) => <TableRow key={job.id}><TableCell className="font-medium">{job.type}</TableCell><TableCell><StatusBadge status={job.status} label={job.status} /></TableCell><TableCell>{job.retries}/{job.max_retries}</TableCell><TableCell><time>{new Intl.DateTimeFormat(locale === 'tr' ? 'tr-TR' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(job.updated_at))}</time></TableCell><TableCell className="technical-id">{job.id.slice(0, 12)}…</TableCell></TableRow>)}</TableBody></Table></Panel>
      )}
    </div>
  )
}
