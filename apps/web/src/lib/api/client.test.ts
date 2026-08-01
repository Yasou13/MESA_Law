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
