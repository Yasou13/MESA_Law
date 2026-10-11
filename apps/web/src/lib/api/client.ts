import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import { getSession, signOut } from 'next-auth/react'

export interface ApiProblem {
  detail?: string | Array<{ msg?: string }>
  title?: string
  message?: string
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number | undefined,
    public readonly problem: ApiProblem | undefined,
    public readonly referenceId: string | undefined,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface ApiResponseMetadata {
  traceId?: string
  requestId?: string
  correlationId?: string
}

const responseMetadata = new WeakMap<object, ApiResponseMetadata>()

function responseHeader(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

export function getApiResponseMetadata(value: unknown): ApiResponseMetadata | undefined {
  if ((typeof value !== 'object' || value === null) && typeof value !== 'function') {
    return undefined
  }
  return responseMetadata.get(value)
}

function apiOrigin(): string {
  const configured = process.env.NEXT_PUBLIC_MESA_LAW_API_BASE_URL?.trim()
  if (!configured) return ''
  return configured.replace(/\/$/, '').replace(/\/api\/v1$/, '')
}

function javaApiOrigin(): string | undefined {
  const configured = process.env.NEXT_PUBLIC_MESA_LAW_JAVA_API_BASE_URL?.trim()
  if (!configured) return undefined
  return configured.replace(/\/$/, '').replace(/\/api\/v1$/, '')
}

// Keep this an explicit allowlist: endpoints absent from Spring stay on the existing API.
function javaEndpoint(
  url: string | undefined,
  method: string | undefined,
  params: unknown,
): string | undefined {
  if (!url?.startsWith('/')) return undefined

  const path = url.split('?')[0]
  const verb = (method ?? 'GET').toUpperCase()
  const apiPath = path.startsWith('/api/v1/') ? path.slice('/api/v1'.length) : undefined

  if (path === '/' && verb === 'GET') return '/'
  if (path === '/api/v1/dashboard/metrics' && verb === 'GET') return path
  if (!apiPath) return undefined

  const supports = (route: string, ...verbs: string[]) => route === apiPath && verbs.includes(verb)

  if (supports('/session/context', 'GET') || supports('/session/active-firm', 'POST')) return apiPath
  if (supports('/users/me', 'GET', 'PUT') || supports('/users/me/support-access', 'POST')) return apiPath
  if (supports('/firms', 'GET', 'POST') || supports('/firms/members', 'GET')) return apiPath
  if (/^\/firms\/[^/]+$/.test(apiPath) && verb === 'GET') return apiPath
  if (/^\/firms\/[^/]+\/members\/[^/]+\/role$/.test(apiPath) && verb === 'PUT') return apiPath

  if (supports('/matters', 'GET', 'POST')) return apiPath
  if (/^\/matters\/[^/]+$/.test(apiPath) && verb === 'GET') return apiPath
  if (/^\/matters\/[^/]+\/(parties|claims|evidence|claims-evidence|timeline)$/.test(apiPath) && verb === 'GET') {
    return apiPath
  }
  if (/^\/matters\/[^/]+\/mesa-binding$/.test(apiPath) && ['GET', 'PUT'].includes(verb)) return apiPath

  if (supports('/deadlines', 'GET') || (/^\/deadlines\/[^/]+\/complete$/.test(apiPath) && verb === 'POST')) {
    return apiPath
  }
  if (supports('/documents', 'GET') || supports('/documents/upload-intent', 'POST')) return apiPath
  if (/^\/documents\/matters\/[^/]+$/.test(apiPath) && verb === 'GET') return apiPath
  if (/^\/documents\/[^/]+$/.test(apiPath) && verb === 'GET') return apiPath
  if (/^\/documents\/[^/]+\/(complete|download)$/.test(apiPath)) {
    const action = apiPath.slice(apiPath.lastIndexOf('/') + 1)
    if ((action === 'complete' && verb === 'POST') || (action === 'download' && verb === 'GET')) return apiPath
  }

  if (apiPath === '/draft-studio/drafts' && ['GET', 'POST'].includes(verb)) return '/drafts'
  if (apiPath === '/draft-studio/drafts/generate' && verb === 'POST') return '/drafts/generate'
  const matterDrafts = apiPath.match(/^\/draft-studio\/drafts\/matter\/([^/]+)$/)
  if (matterDrafts && verb === 'GET') return `/drafts/matters/${matterDrafts[1]}`
  const draftAction = apiPath.match(/^\/draft-studio\/drafts\/([^/]+)\/(approve|citations|export|submit-review)$/)
  if (draftAction) {
    const [, draftId, action] = draftAction
    const supported =
      (action === 'citations' && verb === 'GET') ||
      (['approve', 'export', 'submit-review'].includes(action) && verb === 'POST')
    if (supported) return `/drafts/${draftId}/${action}`
  }
  const draft = apiPath.match(/^\/draft-studio\/drafts\/([^/]+)$/)
  if (draft && draft[1] !== 'generate' && ['GET', 'PUT'].includes(verb)) return `/drafts/${draft[1]}`

  if (apiPath === '/reviews' && verb === 'GET' && getParam(params, 'matter_id')) {
    return `/reviews/matters/${encodeURIComponent(String(getParam(params, 'matter_id')))}`
  }
  if (/^\/reviews\/[^/]+\/(approve|reject|correct)$/.test(apiPath) && verb === 'POST') return apiPath
  if (supports('/audit/events', 'GET')) return apiPath
  if (supports('/operations/jobs', 'GET') || supports('/operations/metrics', 'GET')) return apiPath
  if (supports('/qa/ask', 'POST')) return apiPath
  if (supports('/research/start', 'POST') || supports('/research/search', 'GET')) return apiPath
  if (supports('/notifications', 'GET')) return apiPath
  if (/^\/notifications\/[^/]+\/read$/.test(apiPath) && verb === 'POST') return apiPath

  const parsedDocuments = apiPath.match(/^\/parser\/document\/([^/]+)$/)
  if (parsedDocuments && verb === 'GET') return `/parsed/document/${parsedDocuments[1]}`
  const parsedPages = apiPath.match(/^\/parser\/([^/]+)\/pages$/)
  if (parsedPages && verb === 'GET') return `/parsed/${parsedPages[1]}/pages`

  return undefined
}

function getParam(params: unknown, key: string): unknown {
  if (params instanceof URLSearchParams) return params.get(key) ?? undefined
  if (typeof params === 'object' && params !== null && key in params) {
    return (params as Record<string, unknown>)[key]
  }
  return undefined
}

function mapObjectKeys(value: unknown, mapKey: (key: string) => string): unknown {
  if (Array.isArray(value)) return value.map((item) => mapObjectKeys(item, mapKey))
  if (typeof value !== 'object' || value === null) return value

  const prototype = Object.getPrototypeOf(value)
  if (prototype !== Object.prototype && prototype !== null) return value

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [mapKey(key), mapObjectKeys(item, mapKey)]),
  )
}

function toJavaProperty(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, character: string) => character.toUpperCase())
}

function toFrontendProperty(key: string): string {
  return key.replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase()
}

function parseReviewPayloads(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(parseReviewPayloads)
  if (typeof value !== 'object' || value === null) return value

  const prototype = Object.getPrototypeOf(value)
  if (prototype !== Object.prototype && prototype !== null) return value

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => {
      if ((key === 'proposedContent' || key === 'correctedContent') && typeof item === 'string') {
        try {
          return [key, parseReviewPayloads(JSON.parse(item) as unknown)]
        } catch {
          return [key, item]
        }
      }
      return [key, parseReviewPayloads(item)]
    }),
  )
}

function prepareJavaRequest(value: unknown, path: string): unknown {
  if (/^\/reviews\/[^/]+\/correct$/.test(path) && typeof value === 'object' && value !== null) {
    const request = value as Record<string, unknown>
    const { corrected_content: correctedContent, ...rest } = request
    const javaRest = mapObjectKeys(rest, toJavaProperty) as Record<string, unknown>
    return {
      ...javaRest,
      correctedContent: JSON.stringify(correctedContent ?? {}),
    }
  }
  return mapObjectKeys(value, toJavaProperty)
}

function normalizeJavaResponse(value: unknown, path: string): unknown {
  const responseValue = path.startsWith('/reviews/') ? parseReviewPayloads(value) : value
  const normalized = mapObjectKeys(responseValue, (key) => {
    if (path.startsWith('/deadlines') && key === 'completed') return 'is_completed'
    if (path === '/firms/members' && key === 'active') return 'is_active'
    if (/^\/matters\/[^/]+\/timeline$/.test(path)) {
      if (key === 'eventDate') return 'date'
      if (key === 'eventType') return 'title'
      if (key === 'sourceType') return 'source'
    }
    return toFrontendProperty(key)
  })

  if (
    path === '/operations/metrics' &&
    typeof normalized === 'object' && normalized !== null &&
    typeof value === 'object' && value !== null
  ) {
    const rawStatuses = (value as Record<string, unknown>).mesaMutationTerminalStatuses
    if (typeof rawStatuses === 'object' && rawStatuses !== null) {
      const metrics = normalized as Record<string, unknown>
      metrics.mesa_mutation_terminal_statuses = rawStatuses
    }
  }

  if (/^\/matters\/[^/]+\/timeline$/.test(path) && Array.isArray(normalized)) {
    return normalized.map((event) => {
      if (typeof event !== 'object' || event === null) return event
      const timelineEvent = event as Record<string, unknown>
      return {
        ...timelineEvent,
        confidence: typeof timelineEvent.confidence === 'string' ? timelineEvent.confidence : 'unknown',
      }
    })
  }

  if (path === '/qa/ask' && typeof normalized === 'object' && normalized !== null) {
    const response = normalized as Record<string, unknown>
    if (Array.isArray(response.sources) && !Array.isArray(response.citations)) {
      response.citations = response.sources
    }
    if (typeof response.status !== 'string') response.status = 'DEGRADED'
    if (typeof response.retrieval !== 'object' || response.retrieval === null) {
      response.retrieval = {
        engine: 'NONE',
        scope: 'MATTER',
        verified_document_count: 0,
        verified_citation_count: Array.isArray(response.citations) ? response.citations.length : 0,
        duration_ms: 0,
      }
    }
  }

  return normalized
}

function problemMessage(error: AxiosError<ApiProblem>): string {
  const problem = error.response?.data
  if (typeof problem?.detail === 'string') return problem.detail
  if (Array.isArray(problem?.detail)) {
    return problem.detail.map((issue) => issue.msg ?? 'Validation error').join(', ')
  }
  return problem?.message ?? problem?.title ?? error.message
}

export const AXIOS_INSTANCE = axios.create({
  baseURL: apiOrigin(),
  timeout: 30_000,
  withCredentials: true,
})

AXIOS_INSTANCE.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const headers = AxiosHeaders.from(config.headers)
    if (typeof window !== 'undefined') {
      const session = await getSession()
      if (session?.accessToken) {
        headers.set('Authorization', `Bearer ${session.accessToken}`)
      }
      const method = config.method?.toUpperCase()
      if (
        method &&
        ['POST', 'PUT', 'PATCH'].includes(method) &&
        !headers.has('Idempotency-Key')
      ) {
        headers.set('Idempotency-Key', crypto.randomUUID())
      }
    }
    config.headers = headers
    return config
  },
)

AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  async (unknownError: unknown) => {
    if (!axios.isAxiosError<ApiProblem>(unknownError)) {
      return Promise.reject(unknownError)
    }
    const referenceId =
      unknownError.response?.headers['x-reference-id'] ??
      unknownError.response?.headers['x-correlation-id'] ??
      unknownError.response?.headers['x-trace-id']
    const error = new ApiError(
      problemMessage(unknownError),
      unknownError.response?.status,
      unknownError.response?.data,
      typeof referenceId === 'string' ? referenceId : undefined,
    )
    if (error.status === 401 && typeof window !== 'undefined') {
      await signOut({ redirect: true, callbackUrl: '/login' })
    }
    return Promise.reject(error)
  },
)

export const customInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): Promise<T> => {
  const headers = {
    ...config.headers,
    ...options?.headers,
  }
  const requestConfig: AxiosRequestConfig = { ...config, ...options, headers }
  const javaBaseURL = javaApiOrigin()
  const javaPath = javaBaseURL
    ? javaEndpoint(requestConfig.url, requestConfig.method, requestConfig.params)
    : undefined

  if (javaPath) {
    requestConfig.baseURL = javaBaseURL
    requestConfig.url = javaPath
    requestConfig.data = prepareJavaRequest(requestConfig.data, javaPath)
    requestConfig.params = mapObjectKeys(requestConfig.params, toJavaProperty) as AxiosRequestConfig['params']
  }

  return AXIOS_INSTANCE.request<T>(requestConfig).then(
    (response) => {
      const data = (javaPath ? normalizeJavaResponse(response.data, javaPath) : response.data) as T
      if ((typeof data === 'object' && data !== null) || typeof data === 'function') {
        responseMetadata.set(data, {
          traceId: responseHeader(response.headers['x-trace-id']),
          requestId: responseHeader(response.headers['x-request-id']),
          correlationId: responseHeader(response.headers['x-correlation-id']),
        })
      }
      return data
    },
  )
}

export type ErrorType<Error> = AxiosError<Error>
export type BodyType<BodyData> = BodyData
