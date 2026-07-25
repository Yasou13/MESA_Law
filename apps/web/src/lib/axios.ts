import Axios, { AxiosRequestConfig } from 'axios';

export const AXIOS_INSTANCE = Axios.create({ baseURL: 'http://localhost:8001' });

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
