import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface TableSkeletonProps {
  columns?: number
  rows?: number
  showAvatar?: boolean
}

export function TableSkeleton({ columns = 4, rows = 5, showAvatar = false }: TableSkeletonProps) {
  return (
    <div className="rounded-xl border border-[var(--border-surface)] overflow-hidden glass-card">
      <Table>
        <TableHeader className="bg-[var(--bg-surface-hover)]">
          <TableRow>
            {Array.from({ length: columns }).map((_, i) => (
              <TableHead key={i}>
                <Skeleton className="h-4 w-24 bg-[var(--border-surface)]" />
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <TableRow key={rowIndex} className="border-b-[var(--border-surface)]">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <TableCell key={colIndex}>
                  <div className="flex items-center gap-3">
                    {colIndex === 0 && showAvatar && (
                      <Skeleton className="h-8 w-8 rounded-full bg-[var(--border-surface)]" />
                    )}
                    <Skeleton className={`h-4 bg-[var(--border-surface)] ${
                      colIndex === 0 ? 'w-32' : colIndex === columns - 1 ? 'w-16 ml-auto' : 'w-24'
                    }`} />
                  </div>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
