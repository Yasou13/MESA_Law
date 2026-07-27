import Axios, { AxiosRequestConfig } from 'axios';

const baseURL = process.env.NEXT_PUBLIC_MESA_LAW_API_BASE_URL || '/api';
export const AXIOS_INSTANCE = Axios.create({ baseURL });

import { getSession } from 'next-auth/react';

AXIOS_INSTANCE.interceptors.request.use(async (config) => {
  if (typeof window !== 'undefined') {
    const session = await getSession();
    if (session && (session as any).accessToken) {
      config.headers['Authorization'] = `Bearer ${(session as any).accessToken}`;
    }
  }
  return config;
});

import { toast } from 'react-hot-toast';

AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined') {
      const status = error.response?.status;
      const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';
      
      if (status === 401) {
        // Handled by NextAuth/session expiry
      } else if (status === 403) {
        toast.error('Permission denied: You cannot access this resource.');
      } else if (status === 404) {
        toast.error('Resource not found.');
      } else if (status === 422) {
        toast.error(`Validation error: ${JSON.stringify(message)}`);
      } else if (status >= 500) {
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
  
  // Map fetch semantics to Axios
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
