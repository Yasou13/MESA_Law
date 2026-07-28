import Axios, { AxiosRequestConfig, AxiosError } from 'axios';
import { getSession, signOut } from 'next-auth/react';
import { toast } from 'react-hot-toast';
import type { Session } from 'next-auth';

// Base URL empty string so it resolves to current origin, preventing double /api/v1
const baseURL = process.env.NEXT_PUBLIC_MESA_LAW_API_BASE_URL || '';
export const AXIOS_INSTANCE = Axios.create({ baseURL });

// Request Interceptor
AXIOS_INSTANCE.interceptors.request.use(async (config) => {
  if (typeof window !== 'undefined') {
    const session = await getSession() as Session | null;
    if (session) {
      if (session.accessToken) {
        config.headers['Authorization'] = `Bearer ${session.accessToken}`;
      }
      if (session.activeFirmId) {
        config.headers['x-tenant-id'] = session.activeFirmId;
      }
    }
  }
  return config;
});

// Response Interceptor
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (typeof window !== 'undefined') {
      const status = error.response?.status;
      const data = error.response?.data as any;
      const headers = error.response?.headers || {};
      
      const referenceId = headers['x-reference-id'] || headers['x-correlation-id'];
      const refSuffix = referenceId ? ` (Ref: ${referenceId})` : '';
      
      let message = 'An unexpected error occurred';
      
      // Handle application/problem+json and standard FastAPI ValidationErrors
      if (data && data.detail) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
        }
      } else if (error.message) {
        message = error.message;
      }
      
      message += refSuffix;
      
      if (status === 401) {
        toast.error('Session expired. Please log in again.');
        await signOut({ redirect: true, callbackUrl: '/login' });
      } else if (status === 403) {
        toast.error(`Permission denied: ${message}`);
      } else if (status === 404) {
        toast.error(`Resource not found: ${message}`);
      } else if (status === 409) {
        toast.error(`Conflict: ${message}`);
      } else if (status === 422) {
        toast.error(`Validation error: ${message}`);
      } else if (status === 429) {
        toast.error(`Rate limited: Please wait before trying again.${refSuffix}`);
      } else if (status === 503) {
        toast.error(`Service unavailable: ${message}`);
      } else if (status && status >= 500) {
        toast.error(`Server error: ${message}`);
      } else {
        toast.error(message);
      }
    }
    return Promise.reject(error);
  }
);

export const customInstance = <T>(
  url: string,
  options?: any,
): Promise<T> => {
  const source = Axios.CancelToken.source();
  
  const mappedConfig: AxiosRequestConfig = { 
    url,
    method: options?.method || 'GET',
    headers: options?.headers,
    cancelToken: source.token 
  };

  if (options?.body) {
    try {
      mappedConfig.data = JSON.parse(options.body);
    } catch {
      mappedConfig.data = options.body;
    }
  }

  const promise = AXIOS_INSTANCE(mappedConfig).then((response) => {
    return { data: response.data, status: response.status, headers: response.headers } as unknown as T;
  });

  // @ts-expect-error adding cancel to promise
  promise.cancel = () => {
    source.cancel('Query was cancelled');
  };

  return promise;
};
