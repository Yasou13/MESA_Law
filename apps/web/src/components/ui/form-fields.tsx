import * as React from 'react'
import { UseFormReturn } from 'react-hook-form'
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

interface BaseFieldProps {
  form: UseFormReturn<any>
  name: string
  label: string
  description?: string
  placeholder?: string
}

export function TextField({ form, name, label, description, placeholder, type = 'text', ...props }: BaseFieldProps & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Input type={type} placeholder={placeholder} {...field} {...props} className="bg-[var(--background)] border-[var(--border-surface)]" />
          </FormControl>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage className="text-[var(--color-semantic-error)]" />
        </FormItem>
      )}
    />
  )
}

export function TextAreaField({ form, name, label, description, placeholder, ...props }: BaseFieldProps & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Textarea placeholder={placeholder} {...field} {...props} className="bg-[var(--background)] border-[var(--border-surface)] resize-none" />
          </FormControl>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage className="text-[var(--color-semantic-error)]" />
        </FormItem>
      )}
    />
  )
}

interface SelectOption {
  label: string
  value: string
}

export function SelectField({ form, name, label, description, placeholder, options }: BaseFieldProps & { options: SelectOption[] }) {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <Select onValueChange={field.onChange} defaultValue={field.value}>
            <FormControl>
              <SelectTrigger className="bg-[var(--background)] border-[var(--border-surface)]">
                <SelectValue placeholder={placeholder} />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage className="text-[var(--color-semantic-error)]" />
        </FormItem>
      )}
    />
  )
}
