'use client'

import { useEffect } from 'react'
import { AlertCircle } from 'lucide-react'

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Protected layout error:', error)
  }, [error])

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] p-6 text-center">
      <div className="w-16 h-16 bg-[var(--color-semantic-error)]/10 text-[var(--color-semantic-error)] rounded-full flex items-center justify-center mb-6">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h2 className="text-2xl font-bold text-[var(--foreground)] mb-2">Something went wrong!</h2>
      <p className="text-[var(--color-anthracite-400)] max-w-md mb-8">
        {error.message || 'An unexpected error occurred in this module.'}
      </p>
      <button
        onClick={() => reset()}
        className="px-6 py-3 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] text-white font-medium rounded-xl transition-all"
      >
        Try again
      </button>
    </div>
  )
}
