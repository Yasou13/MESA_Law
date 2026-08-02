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
  return AXIOS_INSTANCE.request<T>({ ...config, ...options, headers }).then(
    (response) => {
      const data = response.data
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
