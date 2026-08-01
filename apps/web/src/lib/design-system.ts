export type Theme = 'light' | 'dark'

export type AsyncViewState = 'loading' | 'empty' | 'error' | 'degraded' | 'ready'

export interface DocumentFocus {
  documentId: string
  revisionId: string
  pageNumber: number | null
  chunkId: string
  textStart: number
  textEnd: number
}

export interface CitationViewModel extends DocumentFocus {
  documentTitle: string
  evidenceExcerpt: string
  evidenceSha256: string
  lowProvenance: boolean
  provenanceState: string
  relevanceScore: number | null
}
