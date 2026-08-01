export type AppLocale = 'tr' | 'en'

export function pathnameWithoutLocale(pathname: string): string {
  const stripped = pathname.replace(/^\/(?:tr|en)(?=\/|$)/, '')
  return stripped || '/'
}

export function localizedHref(locale: AppLocale, href: string): string {
  const normalized = href.startsWith('/') ? href : `/${href}`
  return locale === 'en' ? `/en${normalized === '/' ? '' : normalized}` : normalized
}
