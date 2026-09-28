package com.mesalaw.security;

import java.util.Set;

/**
 * Holds the resolved request context (tenant, principal, roles) for the current request.
 * Replaces Python's {@code RequestContext} from core/models.py.
 *
 * <p>Populated by the TenantContextFilter and available throughout the request lifecycle.</p>
 */
public record RequestContext(
        String tenantId,
        String principalId,
        Set<String> roles
) {
    /**
     * Returns true if the current user has the specified role.
     */
    public boolean hasRole(String role) {
        return roles != null && roles.contains(role);
    }

    /**
     * Returns true if the current user has any of the specified roles.
     */
    public boolean hasAnyRole(Set<String> allowedRoles) {
        if (roles == null || allowedRoles == null) return false;
        for (String role : allowedRoles) {
            if (roles.contains(role)) return true;
        }
        return false;
    }
}
