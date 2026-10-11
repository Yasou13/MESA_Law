import { withAuth, type NextRequestWithAuth } from 'next-auth/middleware'
import createMiddleware from 'next-intl/middleware'
import { NextResponse, type NextFetchEvent, type NextRequest } from 'next/server'

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
    secret: process.env.NEXTAUTH_SECRET,
    callbacks: {
      authorized: ({ token }) => testAuthBypass || Boolean(token),
    },
    pages: { signIn: '/login' },
  },
)

export default async function proxy(request: NextRequest, event: NextFetchEvent) {
  if (request.headers.has('x-next-intl-locale')) {
    return NextResponse.next()
  }

  if (request.nextUrl.pathname === '/tr/login') return NextResponse.next()
  if (request.nextUrl.pathname === '/login') {
    const localizedUrl = request.nextUrl.clone()
    localizedUrl.pathname = '/tr/login'
    return NextResponse.rewrite(localizedUrl)
  }
  if (isLoginPath(request.nextUrl.pathname)) return intlMiddleware(request)

  return authMiddleware(request as NextRequestWithAuth, event)
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
}
