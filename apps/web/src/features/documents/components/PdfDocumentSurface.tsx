'use client'

import { useLayoutEffect, useRef, useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import { Document as PDFDocument, Page, pdfjs } from 'react-pdf'
import { useTranslations } from 'next-intl'

import { InlineAlert } from '@/components/ui/inline-alert'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface PdfHighlight {
  x0: number
  y0: number
  x1: number
  y1: number
}

interface PdfDocumentSurfaceProps {
  file: string
  pageNumber: number
  highlight?: PdfHighlight | null
  onPageCount: (count: number) => void
}

export default function PdfDocumentSurface({
  file,
  pageNumber,
  highlight,
  onPageCount,
}: PdfDocumentSurfaceProps) {
  const t = useTranslations('Viewer')
  const containerRef = useRef<HTMLDivElement>(null)
  const [renderWidth, setRenderWidth] = useState(720)
  const [viewport, setViewport] = useState<{ width: number; height: number } | null>(null)
  const [loadError, setLoadError] = useState(false)

  useLayoutEffect(() => {
    const container = containerRef.current
    if (!container) return
    const resize = () => setRenderWidth(Math.max(280, Math.min(container.clientWidth - 32, 920)))
    resize()
    const observer = new ResizeObserver(resize)
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  if (loadError) {
    return (
      <div className="p-6">
        <InlineAlert tone="danger" title={t('pdfLoadError')}>
          <p>{t('pdfLoadErrorDescription')}</p>
        </InlineAlert>
      </div>
    )
  }

  const highlightStyle =
    highlight && viewport
      ? {
          left: `${(highlight.x0 / viewport.width) * 100}%`,
          top: `${(highlight.y0 / viewport.height) * 100}%`,
          width: `${((highlight.x1 - highlight.x0) / viewport.width) * 100}%`,
          height: `${((highlight.y1 - highlight.y0) / viewport.height) * 100}%`,
        }
      : null
  const renderHeight = renderWidth * (viewport ? viewport.height / viewport.width : 792 / 612)

  return (
    <div ref={containerRef} tabIndex={0} aria-label={t('pdfViewport')} className="h-full overflow-auto bg-surface-subtle p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus">
      <PDFDocument
        file={file}
        loading={
          <div className="flex min-h-96 items-center justify-center gap-2 text-foreground-secondary" role="status">
            <Loader2 className="size-5 animate-spin" aria-hidden="true" />{t('pdfPreparing')}
          </div>
        }
        error={
          <div className="flex min-h-96 items-center justify-center gap-2 text-danger">
            <AlertTriangle className="size-5" aria-hidden="true" />{t('pdfOpenError')}
          </div>
        }
        onLoadSuccess={({ numPages }) => {
          setLoadError(false)
          onPageCount(numPages)
        }}
        onLoadError={() => setLoadError(true)}
      >
        <div
          className="relative mx-auto overflow-hidden border border-border bg-white shadow-raised"
          style={{ width: renderWidth, height: renderHeight }}
        >
          <Page
            key={`${file}:${pageNumber}`}
            pageNumber={pageNumber}
            width={renderWidth}
            renderAnnotationLayer={false}
            renderTextLayer={false}
            onLoadSuccess={(page) => {
              const nextViewport = page.getViewport({ scale: 1 })
              setViewport({ width: nextViewport.width, height: nextViewport.height })
            }}
          />
          {highlightStyle && (
            <div
              role="img"
              aria-label={t('verifiedHighlight')}
              className="pointer-events-none absolute border-2 border-warning bg-warning/25 shadow-sm"
              style={highlightStyle}
            />
          )}
        </div>
      </PDFDocument>
    </div>
  )
}
