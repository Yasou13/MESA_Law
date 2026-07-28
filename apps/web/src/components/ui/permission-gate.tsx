'use client'

import React from 'react'
import { usePermissions, PermissionAction, PermissionResource } from '@/hooks/use-permissions'

interface PermissionGateProps {
  children: React.ReactNode
  action: PermissionAction
  resource: PermissionResource
  fallback?: React.ReactNode
}

export function PermissionGate({ children, action, resource, fallback = null }: PermissionGateProps) {
  const { hasPermission } = usePermissions()

  if (hasPermission(action, resource)) {
    return <>{children}</>
  }

  return <>{fallback}</>
}
