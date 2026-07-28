import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { toast } from 'react-hot-toast';

// 1. Zod Schema
const draftSchema = z.object({
  title: z.string().min(5, "Title must be at least 5 characters").max(100, "Title is too long"),
  content: z.string().min(20, "Content must be at least 20 characters for a valid legal draft"),
});

type DraftFormValues = z.infer<typeof draftSchema>;

interface DraftCreateFormProps {
  onSubmitSuccess: (data: DraftFormValues) => void;
  onCancel: () => void;
}

export function DraftCreateForm({ onSubmitSuccess, onCancel }: DraftCreateFormProps) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<DraftFormValues>({
    resolver: zodResolver(draftSchema),
    defaultValues: {
      title: 'New Legal Draft',
      content: ''
    }
  });

  const onSubmit = async (data: DraftFormValues) => {
    try {
      // Simulate API call or delegate to parent
      await new Promise(resolve => setTimeout(resolve, 500));
      onSubmitSuccess(data);
    } catch (error) {
      toast.error("Failed to create draft");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 bg-zinc-900 p-6 rounded-xl border border-zinc-800">
      <h3 className="text-lg font-semibold text-white mb-4">Create New Draft</h3>
      
      <div>
        <label className="block text-sm font-medium text-zinc-400 mb-1">Draft Title</label>
        <input 
          {...register('title')} 
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-blue-500"
          placeholder="e.g. Service Agreement"
        />
        {errors.title && <p className="text-red-400 text-xs mt-1">{errors.title.message}</p>}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-zinc-400 mb-1">Initial Content</label>
        <textarea 
          {...register('content')} 
          rows={6}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 font-mono text-sm focus:outline-none focus:border-blue-500"
          placeholder="Enter initial clauses..."
        />
        {errors.content && <p className="text-red-400 text-xs mt-1">{errors.content.message}</p>}
      </div>
      
      <div className="flex justify-end gap-3 pt-2">
        <button 
          type="button" 
          onClick={onCancel}
          className="px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          Cancel
        </button>
        <button 
          type="submit" 
          disabled={isSubmitting}
          className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          {isSubmitting ? 'Creating...' : 'Create Draft'}
        </button>
      </div>
    </form>
  );
}
