'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import axios from 'axios'
import { SessionProvider, useSession } from 'next-auth/react'

function AxiosInterceptor({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession()

  useEffect(() => {
    axios.defaults.baseURL = 'http://localhost:8001';
    
    const requestInterceptor = axios.interceptors.request.use((config) => {
      if (session?.accessToken) {
        config.headers.Authorization = `Bearer ${session.accessToken}`
      }
      return config;
    });

    return () => {
      axios.interceptors.request.eject(requestInterceptor);
    }
  }, [session]);

  return <>{children}</>
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <AxiosInterceptor>
          {children}
        </AxiosInterceptor>
      </QueryClientProvider>
    </SessionProvider>
  )
}
