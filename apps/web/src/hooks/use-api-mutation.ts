"use client";

import { useState } from "react";
import { ApiError } from "@/services/api-client";
import { toast } from "sonner"; // Assuming sonner is used for toasts, common in modern next apps

interface UseApiMutationOptions<TData, TVariables> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables) => void;
  onMutate?: (variables: TVariables) => void | any; // Return context for optimistic update
  onSettled?: (data: TData | undefined, error: Error | null, variables: TVariables, context: any) => void;
  successMessage?: string | ((data: TData) => string);
  errorMessage?: string | ((error: Error) => string);
  showToasts?: boolean;
}

export function useApiMutation<TData = any, TVariables = any>({
  mutationFn,
  onSuccess,
  onError,
  onMutate,
  onSettled,
  successMessage,
  errorMessage,
  showToasts = true,
}: UseApiMutationOptions<TData, TVariables>) {
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<TData | null>(null);

  const mutate = async (variables: TVariables) => {
    setIsPending(true);
    setError(null);
    let context: any;

    try {
      if (onMutate) {
        context = await onMutate(variables);
      }

      const result = await mutationFn(variables);
      setData(result);
      
      if (showToasts && successMessage) {
        const msg = typeof successMessage === 'function' ? successMessage(result) : successMessage;
        toast.success(msg);
      }

      if (onSuccess) {
        onSuccess(result, variables);
      }

      return result;
    } catch (err: any) {
      setError(err);
      
      if (showToasts) {
        const msg = errorMessage 
          ? (typeof errorMessage === 'function' ? errorMessage(err) : errorMessage)
          : (err instanceof ApiError ? err.message : "Bir hata oluştu");
        toast.error(msg);
      }

      if (onError) {
        onError(err, variables);
      }
      
      throw err;
    } finally {
      setIsPending(false);
      if (onSettled) {
        onSettled(data || undefined, error, variables, context);
      }
    }
  };

  return {
    mutate,
    isPending,
    error,
    data,
  };
}
