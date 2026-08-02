import { redirect } from 'next/navigation'

import { localizedHref } from '@/lib/navigation'

export default async function LegacyClaimsPage({ params }: { params: Promise<{ id: string; locale: 'tr' | 'en' }> }) {
  const { id, locale } = await params
  redirect(localizedHref(locale, `/matters/${id}/evidence`))
}
