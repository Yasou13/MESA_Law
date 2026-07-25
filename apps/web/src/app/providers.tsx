'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import axios from 'axios'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())

  useEffect(() => {
    axios.defaults.baseURL = 'http://localhost:8001';
    // Add default mock tenant
    axios.interceptors.request.use((config) => {
      config.headers['test-tenant'] = localStorage.getItem('tenant_id') || 'test-tenant';
      return config;
    });
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
