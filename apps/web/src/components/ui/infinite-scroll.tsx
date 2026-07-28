'use client'

import React, { useRef, useEffect } from 'react'
import { useIntersectionObserver } from '@/hooks/use-intersection'
import { Loader2 } from 'lucide-react'

interface InfiniteScrollProps {
  onLoadMore: () => void
  hasMore: boolean
  isLoading: boolean
  children: React.ReactNode
}

export function InfiniteScroll({ onLoadMore, hasMore, isLoading, children }: InfiniteScrollProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null)
  const entry = useIntersectionObserver(loadMoreRef, { threshold: 0.1 })

  useEffect(() => {
    if (entry?.isIntersecting && hasMore && !isLoading) {
      onLoadMore()
    }
  }, [entry?.isIntersecting, hasMore, isLoading, onLoadMore])

  return (
    <>
      {children}
      <div ref={loadMoreRef} className="py-4 flex justify-center items-center w-full min-h-[40px]">
        {isLoading && (
          <div className="flex items-center text-[var(--color-anthracite-400)] gap-2 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading more...
          </div>
        )}
        {!hasMore && !isLoading && (
          <div className="text-[var(--color-anthracite-500)] text-sm">No more items to load.</div>
        )}
      </div>
    </>
  )
}
