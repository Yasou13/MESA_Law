import { expect, test, type Route } from '@playwright/test'

const matterId = '11111111-1111-4111-8111-111111111111'
const documentId = '22222222-2222-4222-8222-222222222222'
const revisionId = '33333333-3333-4333-8333-333333333333'
const reviewId = '44444444-4444-4444-8444-444444444444'

const matter = {
  id: matterId,
  title: 'Contract dispute MVP',
  internal_reference: null,
  status: 'ACTIVE',
  client_name: null,
  jurisdiction: null,
  case_type: null,
  confidentiality_level: 'standard',
  ai_processing_policy: 'standard',
  opened_at: null,
  closed_at: null,
  access_scope: 'admin',
  responsible_attorney: 'Law-side E2E Reviewer',
  created_at: '2026-01-02T09:00:00Z',
  updated_at: '2026-01-02T10:00:00Z',
}

const review = () => ({
  id: reviewId,
  matter_id: matterId,
  entity_type: 'CONTRACT_OBLIGATION',
  entity_id: 'assertion-1',
  suggestion_id: 'suggestion-1',
  proposed_content: {
    assertion_type: 'OBLIGATION',
    subject: 'Acme',
    predicate: 'must_pay',
    object: 'Invoice 42',
  },
  corrected_content: null,
  status: reviewStatusForFixture,
  decision_reason: null,
  version_id: reviewStatusForFixture === 'PROPOSED' ? 7 : 8,
})

let reviewStatusForFixture = 'PROPOSED'

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })
}

test('Keycloak entry to bound matter, immutable upload, review and sourced QA', async ({ page }) => {
  let authenticated = false
  let matterCreated = false
  let bindingCreated = false
  let documentCompleted = false
  let reviewStatus = 'PROPOSED'
  reviewStatusForFixture = reviewStatus

  await page.route('**/api/auth/session', async (route) => {
    if (!authenticated) return json(route, null)
    return json(route, {
      user: { name: 'Law-side E2E Reviewer', email: 'reviewer@example.test' },
      accessToken: 'contract-faithful-stub-token',
      expires: new Date(Date.now() + 3_600_000).toISOString(),
    })
  })

  await page.route('**/stub-upload', async (route) => {
    expect(route.request().method()).toBe('PUT')
    expect(await route.request().headerValue('content-type')).toBe('application/pdf')
    await route.fulfill({ status: 200, body: '' })
  })

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const { pathname } = url
    const method = request.method()

    if (method === 'GET' && pathname === '/api/v1/firms') {
      return json(route, [{ id: 'firm-1', name: 'E2E Law Firm' }])
    }
    if (method === 'GET' && pathname === '/api/v1/session/context') {
      return json(route, {
        principal_id: 'reviewer-1',
        roles: ['firm_admin'],
        status: 'active',
        tenant_id: 'firm-1',
      })
    }
    if (method === 'GET' && pathname === '/api/v1/notifications') return json(route, [])
    if (method === 'GET' && pathname === '/api/v1/dashboard/metrics') {
      return json(route, {
        active_matters: matterCreated ? 1 : 0,
        degraded_capabilities: [],
        failed_operations: 0,
        pending_reviews: reviewStatus === 'PROPOSED' ? 1 : 0,
        system_status: 'ok',
        unread_notifications: 0,
        upcoming_deadlines: 0,
      })
    }
    if (method === 'GET' && pathname === '/api/v1/deadlines') return json(route, [])
    if (method === 'GET' && pathname === '/api/v1/reviews') {
      if (!matterCreated) return json(route, [])
      reviewStatusForFixture = reviewStatus
      return json(route, [review()])
    }
    if (method === 'GET' && pathname === `/api/v1/reviews/${reviewId}/context`) {
      reviewStatusForFixture = reviewStatus
      return json(route, {
        review: review(),
        suggestion: {
          id: 'suggestion-1',
          suggestion_type: 'CONTRACT_OBLIGATION',
          extractor_name: 'law-side-fixture',
          extractor_version: '1.0',
          parser_version: 'pymupdf-1',
          confidence_category: 'high',
        },
        source: {
          document_id: documentId,
          document_title: 'contract.pdf',
          revision_id: revisionId,
          page_number: 2,
          chunk_id: 'chunk-contract-2',
          text_start: 14,
          text_end: 47,
          bbox: { x0: 20, y0: 50, x1: 260, y1: 90 },
          evidence_text: 'Acme must pay Invoice 42 within 30 days.',
          evidence_sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
          parser_version: 'pymupdf-1',
          extraction_version: 'fixture-1',
          provenance_state: 'VERIFIED_PDF',
        },
        history: [],
      })
    }
    if (method === 'GET' && pathname === `/api/v1/documents/${documentId}/viewer-context`) {
      return json(route, {
        document: {
          id: documentId,
          matter_id: matterId,
          title: 'contract.pdf',
          status: 'READY',
          latest_revision_id: revisionId,
          provenance_state: 'VERIFIED_PDF',
          failure_reason: null,
          created_at: '2026-01-02T09:00:00Z',
        },
        revision: {
          id: revisionId,
          version: 1,
          mime_type: 'application/pdf',
          size_bytes: 1024,
          sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
          immutable_at: '2026-01-02T09:05:00Z',
          scan_status: 'READY',
          provenance_state: 'VERIFIED_PDF',
        },
        parsed_document: {
          id: 'parsed-1',
          revision_id: revisionId,
          parser: 'pymupdf',
          parsing_revision: 1,
          ocr_version: null,
          pipeline_version: 'fixture-1',
          status: 'completed',
          provenance_state: 'VERIFIED_PDF',
        },
      })
    }
    if (method === 'GET' && pathname === '/api/v1/matters') {
      return json(route, matterCreated ? [matter] : [])
    }
    if (method === 'POST' && pathname === '/api/v1/matters/conflict-check') {
      const body = request.postDataJSON() as { party_names: string[] }
      expect(body.party_names).toEqual(['Acme', 'Globex'])
      return json(route, { id: 'conflict-check-1', conflicts: [], has_conflicts: false })
    }
    if (method === 'POST' && pathname === '/api/v1/matters') {
      expect(await request.headerValue('idempotency-key')).toBeTruthy()
      matterCreated = true
      return json(route, matter, 201)
    }
    if (method === 'GET' && pathname === `/api/v1/matters/${matterId}`) return json(route, matter)
    if (method === 'GET' && pathname === `/api/v1/matters/${matterId}/parties`) return json(route, [])
    if (method === 'GET' && pathname === `/api/v1/matters/${matterId}/claims`) return json(route, [])
    if (method === 'GET' && pathname === `/api/v1/documents/matters/${matterId}`) {
      return json(
        route,
        documentCompleted
          ? [{
              id: documentId,
              matter_id: matterId,
              title: 'contract.pdf',
              status: 'SCANNING',
              latest_revision_id: revisionId,
              provenance_state: 'PENDING',
              failure_reason: null,
              created_at: new Date().toISOString(),
            }]
          : [],
      )
    }
    if (method === 'GET' && pathname === `/api/v1/matters/${matterId}/mesa-binding`) {
      if (!bindingCreated) return json(route, { detail: 'MESA binding not found' }, 404)
      return json(route, {
        id: 'binding-1',
        matter_id: matterId,
        mesa_tenant_id: 'mesa-tenant-1',
        workspace_id: 'workspace-1',
        dataset_id: 'dataset-1',
        agent_id: 'agent-1',
        provisioning_status: 'PENDING_PREFLIGHT',
        last_verified_at: null,
        last_error: null,
        version_id: 1,
      })
    }
    if (method === 'PUT' && pathname === `/api/v1/matters/${matterId}/mesa-binding`) {
      expect(await request.headerValue('idempotency-key')).toBeTruthy()
      expect(request.postDataJSON()).toEqual({
        mesa_tenant_id: 'mesa-tenant-1',
        workspace_id: 'workspace-1',
        dataset_id: 'dataset-1',
        agent_id: 'agent-1',
      })
      bindingCreated = true
      return json(route, {
        id: 'binding-1', matter_id: matterId, ...request.postDataJSON(),
        provisioning_status: 'PENDING_PREFLIGHT', last_verified_at: null, last_error: null, version_id: 1,
      }, 201)
    }
    if (method === 'POST' && pathname === '/api/v1/documents/upload-intent') {
      expect(await request.headerValue('idempotency-key')).toBeTruthy()
      return json(route, {
        document_id: documentId,
        revision_id: revisionId,
        presigned_url: 'http://localhost:3000/stub-upload',
        storage_key: 'quarantine/unique-upload-key',
      })
    }
    if (method === 'POST' && pathname === `/api/v1/documents/${documentId}/complete`) {
      documentCompleted = true
      return json(route, { status: 'SCANNING', revision_id: revisionId })
    }
    if (method === 'POST' && pathname === `/api/v1/reviews/${reviewId}/approve`) {
      expect(await request.headerValue('idempotency-key')).toBeTruthy()
      expect(request.postDataJSON()).toEqual({ expected_version: 7 })
      reviewStatus = 'PUBLISHING'
      reviewStatusForFixture = reviewStatus
      return json(route, {
        id: reviewId,
        status: 'PUBLISHING',
        version_id: 8,
        publication_job_id: 'publish-job-1',
      })
    }
    if (method === 'POST' && pathname === '/api/v1/qa/ask') {
      expect(request.postDataJSON()).toEqual({
        matter_id: matterId,
        question: 'What payment obligation is verified?',
      })
      return json(route, {
        answer: 'Acme must pay Invoice 42.',
        status: 'ANSWERED',
        degraded_reason: null,
        citations: [{
          document_id: documentId,
          revision_id: revisionId,
          page_number: 2,
          chunk_id: 'chunk-contract-2',
          text_start: 14,
          text_end: 47,
          evidence_excerpt: 'Acme must pay Invoice 42 within 30 days.',
          evidence_sha256: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
          provenance_state: 'VERIFIED_PDF',
          low_provenance: false,
          relevance_score: 0.91,
        }],
        retrieval: {
          scope: 'MATTER',
          engine: 'MESA',
          dataset_id: 'dataset-1',
          verified_document_count: 1,
          verified_citation_count: 1,
          duration_ms: 42,
        },
      })
    }

    return json(route, { detail: `Unexpected Law-side stub request: ${method} ${pathname}` }, 500)
  })

  await page.goto('/login')
  await expect(page.getByRole('button', { name: 'Sign in with Keycloak' })).toBeVisible()

  authenticated = true
  await page.reload()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

  await page.getByRole('link', { name: 'Dosyalar', exact: true }).click()
  await page.getByRole('button', { name: 'New Matter' }).click()
  await page.getByLabel('Matter Name').fill(matter.title)
  await page.getByLabel('Parties (comma separated)').fill('Acme, Globex')
  await page.getByRole('button', { name: 'Check Conflicts & Create' }).click()
  await expect(page.getByText(matter.title)).toBeVisible()
  await page.getByText(matter.title).click()

  await page.getByLabel('mesa_tenant_id').fill('mesa-tenant-1')
  await page.getByLabel('workspace_id').fill('workspace-1')
  await page.getByLabel('dataset_id').fill('dataset-1')
  await page.getByLabel('agent_id').fill('agent-1')
  await page.getByRole('button', { name: 'Save binding and run preflight' }).click()
  await expect(page.getByText('PENDING_PREFLIGHT')).toBeVisible()

  await page.getByRole('link', { name: 'Belgeler', exact: true }).last().click()
  await page.locator('input[type="file"]').setInputFiles({
    name: 'contract.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.4\n% contract evidence\n%%EOF'),
  })
  await expect(page.getByText('contract.pdf')).toBeVisible()

  await page.getByRole('link', { name: 'İnceleme Merkezi', exact: true }).click()
  await expect(page.getByText('Acme must pay Invoice 42 within 30 days.')).toBeVisible()
  await page.getByRole('button', { name: 'Onayla', exact: true }).click()
  await page.getByLabel('İnceleme durumu').selectOption('PUBLISHING')
  await expect(page.getByText('PUBLISHING').first()).toBeVisible()

  await page.goto(`/matters/${matterId}/qa`)
  await page.getByPlaceholder('Örneğin: Sözleşmedeki fesih koşulları hangi belgelerde yer alıyor?').fill(
    'What payment obligation is verified?',
  )
  await page.getByRole('button', { name: 'Kaynaklarda ara' }).click()
  await expect(page.getByText('Acme must pay Invoice 42.')).toBeVisible()
  await expect(page.getByText('Sayfa 2')).toBeVisible()
  await expect(page.getByText('Acme must pay Invoice 42 within 30 days.')).toBeVisible()

  await page.goto(`/matters/${matterId}/research`)
  await expect(page.getByRole('heading', { name: 'External legal research unavailable' })).toBeVisible()
})
