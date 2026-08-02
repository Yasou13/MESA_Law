import type { Page, Route } from '@playwright/test'

export const visualMatterId = '11111111-1111-4111-8111-111111111111'
export const visualDocumentId = '22222222-2222-4222-8222-222222222222'
export const visualRevisionId = '33333333-3333-4333-8333-333333333333'
export const visualReviewId = '44444444-4444-4444-8444-444444444444'

const createdAt = '2026-07-28T09:00:00Z'

const matter = {
  id: visualMatterId,
  title: 'Artemis Enerji tedarik uyuşmazlığı',
  internal_reference: 'MESA-2026-0142',
  status: 'ACTIVE',
  client_name: 'Artemis Enerji A.Ş.',
  jurisdiction: 'İstanbul',
  case_type: 'Ticari uyuşmazlık',
  confidentiality_level: 'restricted',
  ai_processing_policy: 'review_required',
  opened_at: '2026-07-12T09:00:00Z',
  closed_at: null,
  access_scope: 'admin',
  responsible_attorney: 'Av. Deniz Yılmaz',
  created_at: createdAt,
  updated_at: '2026-08-01T14:30:00Z',
}

const documents = [
  {
    id: visualDocumentId,
    matter_id: visualMatterId,
    title: 'Ana Tedarik Sözleşmesi — imzalı.pdf',
    status: 'READY',
    latest_revision_id: visualRevisionId,
    provenance_state: 'VERIFIED',
    failure_reason: null,
    created_at: createdAt,
  },
  {
    id: '55555555-5555-4555-8555-555555555555',
    matter_id: visualMatterId,
    title: 'Karşı taraf ihtarnamesi ve teslim teyitleri.docx',
    status: 'PROCESSING',
    latest_revision_id: '66666666-6666-4666-8666-666666666666',
    provenance_state: 'LOW_PROVENANCE',
    failure_reason: null,
    created_at: '2026-07-30T11:15:00Z',
  },
]

const review = {
  id: visualReviewId,
  matter_id: visualMatterId,
  entity_type: 'CONTRACT_OBLIGATION',
  entity_id: 'assertion-visual-1',
  suggestion_id: 'suggestion-visual-1',
  proposed_content: {
    assertion_type: 'OBLIGATION',
    subject: 'Artemis Enerji A.Ş.',
    predicate: 'ödeme_yapmalıdır',
    object: 'Fatura 2026/42 — 30 gün içinde',
  },
  corrected_content: null,
  status: 'PROPOSED',
  decision_reason: null,
  version_id: 7,
}

const jobs = [
  { id: 'job-visual-parse', matter_id: visualMatterId, tenant_id: 'firm-visual', type: 'DOCUMENT_PARSE', status: 'RUNNING', payload: { document_id: visualDocumentId }, retries: 0, max_retries: 5, error_message: null, created_at: createdAt, updated_at: '2026-08-01T14:31:00Z' },
  { id: 'job-visual-mesa', matter_id: visualMatterId, tenant_id: 'firm-visual', type: 'MESA_MUTATION_POLL', status: 'PENDING', payload: { mutation_id: 'mutation-42' }, retries: 1, max_retries: 8, error_message: null, created_at: createdAt, updated_at: '2026-08-01T14:29:00Z' },
  { id: 'job-visual-failed', matter_id: visualMatterId, tenant_id: 'firm-visual', type: 'DOCUMENT_SCAN', status: 'FAILED', payload: { document_id: 'legacy-document' }, retries: 3, max_retries: 3, error_message: 'ClamAV tarama servisi yanıt vermedi; iş terminal duruma alındı.', created_at: createdAt, updated_at: '2026-08-01T13:20:00Z' },
  { id: 'job-visual-success', matter_id: visualMatterId, tenant_id: 'firm-visual', type: 'MESA_SCOPE_PREFLIGHT', status: 'SUCCEEDED', payload: { dataset_id: 'dataset-visual' }, retries: 0, max_retries: 3, error_message: null, created_at: createdAt, updated_at: '2026-08-01T12:00:00Z' },
]

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

function fixturePdf(): Buffer {
  const stream = 'BT /F1 18 Tf 72 700 Td (MESA Law - Verified Evidence) Tj 0 -32 Td /F1 11 Tf (Artemis Enerji shall pay invoice 2026/42 within 30 days.) Tj ET'
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
    `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ]
  let output = '%PDF-1.4\n%MESA\n'
  const offsets = [0]
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(output))
    output += `${index + 1} 0 obj\n${object}\nendobj\n`
  })
  const xref = Buffer.byteLength(output)
  output += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`
  output += offsets.slice(1).map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`).join('')
  output += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`
  return Buffer.from(output)
}

export async function installVisualFixture(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((selectedTheme) => {
    localStorage.setItem('theme', selectedTheme)
    Object.defineProperty(window, '__mesaCls', { value: 0, writable: true })
    Object.defineProperty(window, '__mesaClsEntries', { value: [], writable: true })
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const shift = entry as PerformanceEntry & {
          value?: number
          hadRecentInput?: boolean
          sources?: Array<{ node?: Node | null; previousRect?: DOMRectReadOnly; currentRect?: DOMRectReadOnly }>
        }
        if (!shift.hadRecentInput) {
          window.__mesaCls += shift.value ?? 0
          window.__mesaClsEntries.push({
            value: shift.value ?? 0,
            sources: (shift.sources ?? []).map((source) => ({
              node: source.node instanceof Element ? source.node.outerHTML.slice(0, 180) : null,
              previous: source.previousRect ? { x: source.previousRect.x, y: source.previousRect.y, width: source.previousRect.width, height: source.previousRect.height } : null,
              current: source.currentRect ? { x: source.currentRect.x, y: source.currentRect.y, width: source.currentRect.width, height: source.currentRect.height } : null,
            })),
          })
        }
      }
    }).observe({ type: 'layout-shift', buffered: true })
  }, theme)

  await page.route('**/api/auth/session', (route) => json(route, {
    user: { name: 'Av. Deniz Yılmaz', email: 'deniz.yilmaz@example.test' },
    accessToken: 'visual-fixture-token',
    expires: '2027-01-01T00:00:00Z',
  }))
  await page.route('**/fixture.pdf', (route) => route.fulfill({ status: 200, contentType: 'application/pdf', body: fixturePdf() }))
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const { pathname } = url
    const method = request.method()

    if (method === 'GET' && pathname === '/api/v1/firms') return json(route, [{ id: 'firm-visual', name: 'Yılmaz & Ortakları Hukuk' }])
    if (method === 'GET' && pathname === '/api/v1/session/context') return json(route, { principal_id: 'user-visual', roles: ['firm_admin'], status: 'active', tenant_id: 'firm-visual' })
    if (method === 'GET' && pathname === '/api/v1/notifications') return json(route, [
      { id: 'notification-1', category: 'warning', title: 'İnceleme bekliyor', message: 'Ana Tedarik Sözleşmesi için bir canonical öneri karar bekliyor.', status: 'UNREAD', timestamp: '2026-08-01T14:25:00Z' },
      { id: 'notification-2', category: 'success', title: 'Belge işlendi', message: 'İmzalı sözleşmenin immutable revizyonu doğrulandı.', status: 'READ', timestamp: '2026-08-01T12:00:00Z' },
    ])
    if (method === 'GET' && pathname === '/api/v1/dashboard/metrics') return json(route, { active_matters: 1, degraded_capabilities: ['MESA mutation polling'], failed_operations: 1, pending_reviews: 1, system_status: 'degraded', unread_notifications: 1, upcoming_deadlines: 1 })
    if (method === 'GET' && pathname === '/api/v1/matters') return json(route, [matter])
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}`) return json(route, matter)
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}/parties`) return json(route, [
      { id: 'party-1', matter_id: visualMatterId, name: 'Artemis Enerji A.Ş.', role: 'Müvekkil', type: 'Tüzel kişi' },
      { id: 'party-2', matter_id: visualMatterId, name: 'Kuzey Tedarik Ltd. Şti.', role: 'Karşı taraf', type: 'Tüzel kişi' },
    ])
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}/claims`) return json(route, [
      { id: 'claim-1', matter_id: visualMatterId, description: 'Fatura 2026/42 otuz gün içinde ödenmelidir.', status: 'CANONICAL', review_status: 'APPROVED' },
    ])
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}/timeline`) return json(route, [
      { id: 'timeline-1', date: '2026-07-12T00:00:00Z', title: 'Sözleşme imzalandı', description: 'Taraflar ana tedarik sözleşmesini imzaladı.', source: visualDocumentId, confidence: 'high' },
    ])
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}/evidence`) return json(route, [
      { id: 'evidence-1', matter_id: visualMatterId, description: 'Artemis Enerji, Fatura 2026/42 bedelini 30 gün içinde ödemelidir.', document_id: visualDocumentId, review_status: 'APPROVED', source_locator_id: 'locator-visual-1' },
    ])
    if (method === 'GET' && pathname === '/api/v1/deadlines') return json(route, [{ id: 'deadline-1', matter_id: visualMatterId, description: 'Cevap dilekçesi için son gün', due_date: '2027-01-15T16:00:00Z', is_completed: false }])
    if (method === 'GET' && pathname === '/api/v1/documents') return json(route, documents)
    if (method === 'GET' && pathname === `/api/v1/documents/matters/${visualMatterId}`) return json(route, documents)
    if (method === 'GET' && pathname === `/api/v1/matters/${visualMatterId}/mesa-binding`) return json(route, { id: 'binding-visual', matter_id: visualMatterId, mesa_tenant_id: 'mesa-tenant-visual', workspace_id: 'workspace-visual', dataset_id: 'dataset-visual', agent_id: 'agent-visual', provisioning_status: 'READY', last_verified_at: '2026-08-01T13:00:00Z', last_error: null, version_id: 2 })
    if (method === 'GET' && pathname === '/api/v1/reviews') return json(route, [review])
    if (method === 'GET' && pathname === `/api/v1/reviews/${visualReviewId}/context`) return json(route, {
      review,
      suggestion: { id: 'suggestion-visual-1', suggestion_type: 'CONTRACT_OBLIGATION', extractor_name: 'legal-rule-extractor', extractor_version: '2.1.0', parser_version: 'pymupdf-1.24', confidence_category: 'high' },
      source: { document_id: visualDocumentId, document_title: documents[0].title, revision_id: visualRevisionId, page_number: 1, chunk_id: 'chunk-visual-1', text_start: 0, text_end: 66, bbox: { x0: 70, y0: 70, x1: 540, y1: 120 }, evidence_text: 'Artemis Enerji, Fatura 2026/42 bedelini 30 gün içinde ödemelidir.', evidence_sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', parser_version: 'pymupdf-1.24', extraction_version: 'legal-rule-extractor-2.1.0', provenance_state: 'VERIFIED_PDF' },
      history: [{ id: 'audit-visual-1', action: 'PROPOSED', user_id: 'worker-visual', created_at: createdAt, reason: null }],
    })
    if (method === 'GET' && pathname === `/api/v1/documents/${visualDocumentId}/viewer-context`) return json(route, {
      document: documents[0],
      revision: { id: visualRevisionId, version: 3, mime_type: 'application/pdf', size_bytes: 184320, sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', immutable_at: createdAt, scan_status: 'READY', provenance_state: 'VERIFIED_PDF' },
      parsed_document: { id: 'parsed-visual-1', revision_id: visualRevisionId, parser: 'pymupdf', parsing_revision: 3, ocr_version: null, pipeline_version: 'law-pipeline-2.1', status: 'COMPLETED', provenance_state: 'VERIFIED_PDF' },
    })
    if (method === 'GET' && pathname === '/api/v1/parser/parsed-visual-1/pages') return json(route, [{ id: 'page-visual-1', parsed_document_id: 'parsed-visual-1', page_number: 1, text_content: 'Artemis Enerji, Fatura 2026/42 bedelini 30 gün içinde ödemelidir.', layout_data: { blocks: [{ character_start: 0, character_end: 66, bbox: [70, 70, 540, 120] }] } }])
    if (method === 'GET' && pathname === `/api/v1/documents/${visualDocumentId}/download`) return json(route, { presigned_url: 'http://localhost:3000/fixture.pdf', expires_in_seconds: 300 })
    if (method === 'GET' && pathname === '/api/v1/operations/jobs') return json(route, jobs)
    if (method === 'POST' && pathname === '/api/v1/qa/ask') return json(route, {
      answer: 'Ana sözleşmeye göre Fatura 2026/42 bedeli 30 gün içinde ödenmelidir.', status: 'ANSWERED', degraded_reason: null,
      citations: [{ document_id: visualDocumentId, revision_id: visualRevisionId, page_number: 1, chunk_id: 'chunk-visual-1', text_start: 0, text_end: 66, evidence_excerpt: 'Artemis Enerji, Fatura 2026/42 bedelini 30 gün içinde ödemelidir.', evidence_sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', provenance_state: 'VERIFIED_PDF', low_provenance: false, relevance_score: 0.94 }],
      retrieval: { scope: 'MATTER', engine: 'MESA', dataset_id: 'dataset-visual', verified_document_count: 1, verified_citation_count: 1, duration_ms: 84 },
    }, 200)

    return json(route, { detail: `Unexpected visual fixture request: ${method} ${pathname}` }, 404)
  })
}

declare global {
  interface Window {
    __mesaCls: number
    __mesaClsEntries: Array<{
      value: number
      sources: Array<{
        node: string | null
        previous: { x: number; y: number; width: number; height: number } | null
        current: { x: number; y: number; width: number; height: number } | null
      }>
    }>
  }
}
