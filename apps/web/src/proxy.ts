import { withAuth, type NextRequestWithAuth } from 'next-auth/middleware'
import createMiddleware from 'next-intl/middleware'
import type { NextFetchEvent, NextRequest } from 'next/server'

const locales = ['en', 'tr']
const intlMiddleware = createMiddleware({
  locales,
  defaultLocale: 'tr',
  localePrefix: 'as-needed',
  localeDetection: false,
})

function isLoginPath(pathname: string): boolean {
  return pathname === '/login' || pathname === '/en/login' || pathname === '/tr/login'
}

const testAuthBypass =
  process.env.MESA_LAW_ENVIRONMENT === 'test' && process.env.MESA_LAW_E2E_STUB === '1'

const authMiddleware = withAuth(
  (request) => intlMiddleware(request),
  {
    callbacks: {
      authorized: ({ token }) => testAuthBypass || Boolean(token),
    },
    pages: { signIn: '/login' },
  },
)

export default function proxy(request: NextRequest, event: NextFetchEvent) {
  if (isLoginPath(request.nextUrl.pathname)) return intlMiddleware(request)
  return authMiddleware(request as NextRequestWithAuth, event)
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
}
