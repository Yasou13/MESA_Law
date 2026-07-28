'use client'

import { useEffect } from 'react'
import { AlertOctagon, RotateCcw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-6 bg-[var(--background)]">
      <div className="max-w-md w-full glass-card p-8 rounded-2xl border border-[var(--color-semantic-error)]/20 shadow-xl text-center flex flex-col items-center">
        <div className="w-16 h-16 rounded-full bg-[var(--color-semantic-error)]/10 flex items-center justify-center mb-6 text-[var(--color-semantic-error)]">
          <AlertOctagon className="w-8 h-8" />
        </div>
        
        <h2 className="text-2xl font-bold tracking-tight text-[var(--foreground)] mb-2">Something went wrong!</h2>
        
        <p className="text-[var(--color-anthracite-400)] mb-6 leading-relaxed">
          An unexpected error occurred while rendering this page. Our team has been notified.
        </p>

        <div className="w-full bg-[var(--bg-surface)] border border-[var(--border-surface)] p-3 rounded-lg mb-8 text-left text-xs font-mono text-[var(--color-semantic-error)] overflow-auto max-h-32">
          {error.message || 'Unknown application error'}
          {error.digest && <div className="mt-2 opacity-70">Digest: {error.digest}</div>}
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 w-full justify-center">
          <Button
            onClick={() => reset()}
            className="w-full sm:w-auto gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]"
          >
            <RotateCcw className="w-4 h-4" /> Try again
          </Button>
          <Link href="/dashboard">
            <Button variant="outline" className="w-full sm:w-auto gap-2">
              <Home className="w-4 h-4" /> Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
