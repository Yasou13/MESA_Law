import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  AXIOS_INSTANCE,
  customInstance,
  getApiResponseMetadata,
} from './client'

describe('shared API response metadata', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('keeps successful trace headers beside the returned object', async () => {
    const payload = { status: 'ready' }
    vi.spyOn(AXIOS_INSTANCE, 'request').mockResolvedValue({
      data: payload,
      headers: {
        'x-trace-id': 'trace-123',
        'x-request-id': 'request-123',
        'x-correlation-id': 'correlation-123',
      },
    })

    const response = await customInstance<typeof payload>({ url: '/test' })

    expect(response).toBe(payload)
    expect(getApiResponseMetadata(response)).toEqual({
      traceId: 'trace-123',
      requestId: 'request-123',
      correlationId: 'correlation-123',
    })
  })

  it('does not attempt to attach metadata to primitive responses', async () => {
    vi.spyOn(AXIOS_INSTANCE, 'request').mockResolvedValue({
      data: 'ok',
      headers: { 'x-trace-id': 'trace-123' },
    })

    const response = await customInstance<string>({ url: '/test' })

    expect(response).toBe('ok')
    expect(getApiResponseMetadata(response)).toBeUndefined()
  })
})

describe('Java API routing', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
  })

  function mockRequest(data: unknown) {
    vi.stubEnv('NEXT_PUBLIC_MESA_LAW_JAVA_API_BASE_URL', 'http://java:8002')
    return vi.spyOn(AXIOS_INSTANCE, 'request').mockResolvedValue({ data, headers: {} })
  }

  it('sends snake_case bodies unchanged to Spring (Jackson SNAKE_CASE)', async () => {
    const spy = mockRequest({ id: 'r1', status: 'APPROVED', version_id: 2 })

    await customInstance({
      url: '/api/v1/reviews/r1/approve',
      method: 'POST',
      data: { expected_version: 1, reason: 'looks right' },
    })

    const config = spy.mock.calls[0][0]
    expect(config.baseURL).toBe('http://java:8002')
    expect(config.url).toBe('/reviews/r1/approve')
    expect(config.data).toEqual({ expected_version: 1, reason: 'looks right' })
  })

  it('stringifies corrected_content for review corrections', async () => {
    const spy = mockRequest({ id: 'r1', status: 'CORRECTED', version_id: 2 })

    await customInstance({
      url: '/api/v1/reviews/r1/correct',
      method: 'POST',
      data: { expected_version: 1, reason: 'fix amount', corrected_content: { amount: 150000 } },
    })

    expect(spy.mock.calls[0][0].data).toEqual({
      expected_version: 1,
      reason: 'fix amount',
      corrected_content: '{"amount":150000}',
    })
  })

  it('camelCases query params for @RequestParam binding', async () => {
    const spy = mockRequest([])

    await customInstance({ url: '/api/v1/deadlines', method: 'GET', params: { matter_id: 'm1' } })

    expect(spy.mock.calls[0][0].params).toEqual({ matterId: 'm1' })
  })

  it('parses snake_case review JSON payloads into objects', async () => {
    mockRequest([{ id: 'r1', proposed_content: '{"name":"ABC Ltd"}', corrected_content: null }])

    const response = await customInstance<Array<Record<string, unknown>>>({
      url: '/api/v1/reviews',
      method: 'GET',
      params: { matter_id: 'm1' },
    })

    expect(response[0].proposed_content).toEqual({ name: 'ABC Ltd' })
  })

  it('maps snake_case timeline fields to the frontend contract', async () => {
    mockRequest([{ id: 'e1', event_date: '2026-01-01', event_type: 'HEARING', source_type: 'document' }])

    const response = await customInstance<Array<Record<string, unknown>>>({
      url: '/api/v1/matters/m1/timeline',
      method: 'GET',
    })

    expect(response[0]).toMatchObject({ date: '2026-01-01', title: 'HEARING', source: 'document' })
  })

  it('keeps endpoints without a Java controller on the existing API', async () => {
    const spy = mockRequest({})

    await customInstance({ url: '/api/v1/reviews/r1/context', method: 'GET' })

    expect(spy.mock.calls[0][0].baseURL).toBeUndefined()
  })
})
