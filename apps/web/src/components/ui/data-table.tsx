'use client'

import {
  type ColumnDef,
  type PaginationState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown, Search } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { NoDataState } from '@/components/ui/async-state'
import { cn } from '@/lib/utils'

export interface DataTableCopy {
  search: string
  emptyTitle: string
  emptyDescription: string
  previous: string
  next: string
  page: (current: number, total: number) => string
  rows: (visible: number, total: number) => string
}

interface DataTableProps<TData> {
  columns: ColumnDef<TData, unknown>[]
  data: TData[]
  copy: DataTableCopy
  getRowId?: (row: TData) => string
  initialPageSize?: number
  className?: string
  searchValue?: string
  onSearchChange?: (value: string) => void
  hideSearch?: boolean
  toolbar?: React.ReactNode
}

export function SortableHeader({ label, column }: {
  label: string
  column: { getIsSorted: () => false | 'asc' | 'desc'; toggleSorting: (descending?: boolean) => void }
}) {
  const sorted = column.getIsSorted()
  return (
    <button
      type="button"
      className="-ml-2 inline-flex h-8 items-center gap-1 rounded-md px-2 text-left hover:bg-surface-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
      onClick={() => column.toggleSorting(sorted === 'asc')}
    >
      {label}
      {sorted === 'asc' ? <ChevronDown className="size-3.5 rotate-180" aria-hidden="true" /> : sorted === 'desc' ? <ChevronDown className="size-3.5" aria-hidden="true" /> : <ChevronsUpDown className="size-3.5 text-foreground-muted" aria-hidden="true" />}
    </button>
  )
}

export function DataTable<TData>({
  columns,
  data,
  copy,
  getRowId,
  initialPageSize = 10,
  className,
  searchValue,
  onSearchChange,
  hideSearch = false,
  toolbar,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [internalFilter, setInternalFilter] = useState('')
  const [pagination, setPagination] = useState<PaginationState>({ pageIndex: 0, pageSize: initialPageSize })
  const filter = searchValue ?? internalFilter
  const setFilter = onSearchChange ?? setInternalFilter

  // TanStack Table intentionally returns stateful callbacks; React Compiler skips this hook.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter: filter, pagination },
    onSortingChange: setSorting,
    onGlobalFilterChange: setFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getRowId,
  })

  const filteredCount = table.getFilteredRowModel().rows.length
  const pageCount = Math.max(1, table.getPageCount())

  return (
    <div className={cn('space-y-3', className)}>
      {(!hideSearch || toolbar) && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {!hideSearch && (
            <label className="relative block w-full sm:max-w-sm">
              <span className="sr-only">{copy.search}</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-foreground-muted" aria-hidden="true" />
              <Input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder={copy.search} className="pl-9" />
            </label>
          )}
          {toolbar && <div className="flex flex-wrap items-center gap-2">{toolbar}</div>}
        </div>
      )}

      <div className="max-w-full overflow-auto rounded-lg border border-border bg-surface">
        <table className="w-full min-w-[680px] border-collapse text-[13px] tabular-nums">
          <thead className="sticky top-0 z-10 bg-surface-subtle text-xs text-foreground-secondary">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border">
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="h-10 whitespace-nowrap px-3 text-left font-medium" scope="col">
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b border-border-subtle transition-colors last:border-0 hover:bg-surface-subtle">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="max-w-[32rem] px-3 py-2.5 align-middle text-foreground">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {filteredCount === 0 && (
          <div className="p-6">
            <NoDataState title={copy.emptyTitle} description={copy.emptyDescription} />
          </div>
        )}
      </div>

      {filteredCount > 0 && (
        <div className="flex flex-col gap-2 text-xs text-foreground-secondary sm:flex-row sm:items-center sm:justify-between" aria-live="polite">
          <span>{copy.rows(table.getRowModel().rows.length, filteredCount)}</span>
          <div className="flex items-center gap-2">
            <span>{copy.page(pagination.pageIndex + 1, pageCount)}</span>
            <Button variant="outline" size="icon-sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()} aria-label={copy.previous}>
              <ChevronLeft className="size-4" />
            </Button>
            <Button variant="outline" size="icon-sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()} aria-label={copy.next}>
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
