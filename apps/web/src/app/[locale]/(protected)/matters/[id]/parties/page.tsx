'use client'

import { Search, UsersRound } from 'lucide-react'
import { useLocale } from 'next-intl'
import { use, useMemo, useState } from 'react'

import { useListMatterParties } from '@/api/endpoints/default/default'
import { ErrorState, LoadingState, NoDataState } from '@/components/ui/async-state'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/ui/page-header'
import { Panel } from '@/components/ui/panel'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

export default function MatterPartiesPage({ params }: { params: Promise<{ id: string }> }) {
  const matterId = use(params).id
  const locale = useLocale()
  const [search, setSearch] = useState('')
  const { data: parties = [], isLoading, isError, refetch } = useListMatterParties(matterId)
  const visible = useMemo(() => parties.filter((party) => `${party.name} ${party.role} ${party.type}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())), [parties, search])

  return (
    <div className="space-y-5">
      <PageHeader title={locale === 'tr' ? 'Taraflar' : 'Parties'} description={locale === 'tr' ? 'Dosyayla ilişkili kişi ve kurum kayıtları.' : 'People and organisations associated with this matter.'} />
      <div className="relative max-w-sm"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-foreground-muted" /><Input value={search} onChange={(event) => setSearch(event.target.value)} className="pl-9" placeholder={locale === 'tr' ? 'Taraflarda ara' : 'Search parties'} /></div>
      {isLoading ? <LoadingState /> : isError ? (
        <ErrorState title={locale === 'tr' ? 'Taraflar yüklenemedi' : 'Parties could not be loaded'} description={locale === 'tr' ? 'Verileriniz korunuyor.' : 'Your data remains safe.'} onRetry={() => refetch()} />
      ) : visible.length === 0 ? (
        <NoDataState title={locale === 'tr' ? 'Taraf bulunmuyor' : 'No parties found'} description={search ? (locale === 'tr' ? 'Arama ölçütünü değiştirin.' : 'Change the search criteria.') : (locale === 'tr' ? 'Bu dosyada taraf kaydı bulunmuyor.' : 'This matter has no party records.')} />
      ) : (
        <Panel className="overflow-hidden"><Table><TableHeader><TableRow><TableHead>{locale === 'tr' ? 'Ad' : 'Name'}</TableHead><TableHead>{locale === 'tr' ? 'Rol' : 'Role'}</TableHead><TableHead>{locale === 'tr' ? 'Tür' : 'Type'}</TableHead><TableHead>ID</TableHead></TableRow></TableHeader><TableBody>{visible.map((party) => <TableRow key={party.id}><TableCell className="font-medium"><span className="inline-flex items-center gap-2"><UsersRound className="size-4 text-foreground-muted" />{party.name}</span></TableCell><TableCell>{party.role}</TableCell><TableCell>{party.type}</TableCell><TableCell className="technical-id">{party.id.slice(0, 12)}…</TableCell></TableRow>)}</TableBody></Table></Panel>
      )}
    </div>
  )
}
