import { useSession } from 'next-auth/react'

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'export'
export type PermissionResource = 'matter' | 'document' | 'user' | 'firm' | 'billing'

export function usePermissions() {
  const { data: session } = useSession()

  // In a real implementation, this would check against session.user.roles or session.permissions
  // For the stub implementation, we'll assign full permissions to everyone but demonstrate the concept
  const hasPermission = (action: PermissionAction, resource: PermissionResource): boolean => {
    if (!session?.user) return false
    
    // Example: Read-only role could be implemented as:
    // if (session.user.role === 'viewer' && action !== 'read') return false
    
    return true // Defaulting to true for development
  }

  // A more strict check for break-glass or high-level admin operations
  const isSystemAdmin = (): boolean => {
    return session?.user?.email?.endsWith('@mesalaw.com') ?? false
  }

  return {
    hasPermission,
    isSystemAdmin,
    canEditMatter: hasPermission('update', 'matter'),
    canDeleteMatter: hasPermission('delete', 'matter'),
    canUploadDocument: hasPermission('create', 'document'),
    canDeleteDocument: hasPermission('delete', 'document'),
  }
}
