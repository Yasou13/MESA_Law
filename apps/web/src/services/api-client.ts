import { getSession } from "next-auth/react";

/**
 * Custom API Error to handle HTTP status codes and API error messages.
 */
export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Base fetch wrapper with auth injection, default headers, and error handling.
 */
export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const session = await getSession();
  const token = session?.accessToken;

  const headers = new Headers(options.headers);
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Support for idempotent requests
  if (options.method && ["POST", "PUT", "PATCH"].includes(options.method)) {
    if (!headers.has("Idempotency-Key")) {
      headers.set("Idempotency-Key", crypto.randomUUID());
    }
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";
  const url = endpoint.startsWith("http") ? endpoint : `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    let errorMessage = "An error occurred while fetching the data.";
    
    try {
      errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorData = await response.text();
    }

    throw new ApiError(response.status, errorMessage, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  try {
    return await response.json() as T;
  } catch (error) {
    throw new ApiError(response.status, "Invalid JSON response from server");
  }
}

/**
 * Centralized API client object
 */
export const apiClient = {
  get: <T = any>(endpoint: string, options?: RequestInit) => 
    fetchApi<T>(endpoint, { ...options, method: "GET" }),
    
  post: <T = any>(endpoint: string, data?: any, options?: RequestInit) => 
    fetchApi<T>(endpoint, { 
      ...options, 
      method: "POST", 
      body: data instanceof FormData ? data : JSON.stringify(data) 
    }),
    
  put: <T = any>(endpoint: string, data?: any, options?: RequestInit) => 
    fetchApi<T>(endpoint, { 
      ...options, 
      method: "PUT", 
      body: data instanceof FormData ? data : JSON.stringify(data) 
    }),
    
  patch: <T = any>(endpoint: string, data?: any, options?: RequestInit) => 
    fetchApi<T>(endpoint, { 
      ...options, 
      method: "PATCH", 
      body: data instanceof FormData ? data : JSON.stringify(data) 
    }),
    
  delete: <T = any>(endpoint: string, options?: RequestInit) => 
    fetchApi<T>(endpoint, { ...options, method: "DELETE" }),
};
