'use client'

import { useState } from 'react'
import { ZoomIn, ZoomOut, Maximize2, Download } from 'lucide-react'

interface DocumentViewerProps {
  url: string
  title: string
  onClose: () => void
}

export function DocumentViewer({ url, title, onClose }: DocumentViewerProps) {
  const [zoom, setZoom] = useState(100)

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[var(--background)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface)]">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-medium text-[var(--foreground)]">{title}</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-[var(--bg-surface-hover)] rounded-lg p-1 border border-[var(--border-surface)]">
            <button onClick={() => setZoom(z => Math.max(50, z - 10))} className="p-1.5 hover:bg-[var(--color-anthracite-700)] rounded text-[var(--color-anthracite-300)] hover:text-white transition-colors">
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs font-medium px-2 text-[var(--color-anthracite-200)]">{zoom}%</span>
            <button onClick={() => setZoom(z => Math.min(200, z + 10))} className="p-1.5 hover:bg-[var(--color-anthracite-700)] rounded text-[var(--color-anthracite-300)] hover:text-white transition-colors">
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
          <a href={url} target="_blank" rel="noopener noreferrer" className="p-2 hover:bg-[var(--bg-surface-hover)] rounded-lg text-[var(--color-anthracite-300)] hover:text-white transition-colors border border-transparent hover:border-[var(--border-surface)]">
            <Download className="w-5 h-5" />
          </a>
          <button onClick={onClose} className="px-4 py-2 bg-[var(--color-anthracite-800)] hover:bg-[var(--color-anthracite-700)] text-white rounded-lg text-sm font-medium transition-colors">
            Close Viewer
          </button>
        </div>
      </div>

      {/* Viewer Area */}
      <div className="flex-1 flex overflow-hidden bg-[var(--color-anthracite-900)] p-4 md:p-8">
        <div className="flex-1 bg-white rounded-xl shadow-2xl overflow-hidden flex items-center justify-center relative">
           <iframe 
            src={`${url}#zoom=${zoom}`} 
            className="w-full h-full border-0"
            title={title}
          />
        </div>
      </div>
    </div>
  )
}
