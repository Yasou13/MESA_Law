package com.mesalaw.security;

import java.io.IOException;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.core.annotation.Order;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import com.mesalaw.entity.auth.Membership;
import com.mesalaw.entity.auth.User;
import com.mesalaw.repository.MembershipRepository;
import com.mesalaw.repository.UserRepository;

import jakarta.persistence.EntityManager;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * Filter that resolves the current tenant context from the JWT + cookie,
 * and sets PostgreSQL RLS context via {@code SET LOCAL app.current_tenant}.
 *
 * <p>Replaces Python's {@code setup_tenant_context()} dependency and
 * the SQLAlchemy RLS event listeners from core/rls.py.</p>
 *
 * <h3>Tenant Resolution Order:</h3>
 * <ol>
 *   <li>{@code mesa_active_firm_id} cookie (set by POST /session/active-firm)</li>
 *   <li>First active membership of the authenticated user</li>
 * </ol>
 */
@Component
@Order(1)
@RequiredArgsConstructor
@Slf4j
public class TenantContextFilter extends OncePerRequestFilter {

    private final UserRepository userRepository;
    private final MembershipRepository membershipRepository;
    private final EntityManager entityManager;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.equals("/") ||
               path.startsWith("/health") ||
               path.startsWith("/actuator") ||
               path.equals("/readiness");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth == null || !(auth.getPrincipal() instanceof Jwt jwt)) {
                filterChain.doFilter(request, response);
                return;
            }

            String keycloakId = jwt.getSubject();
            User user = userRepository.findByKeycloakId(keycloakId).orElse(null);
            if (user == null) {
                filterChain.doFilter(request, response);
                return;
            }

            // Resolve tenant from cookie or first active membership
            String tenantId = resolveActiveFirmId(request, user.getId());
            if (tenantId == null) {
                filterChain.doFilter(request, response);
                return;
            }

            // Extract roles from Spring Security authorities
            Set<String> roles = auth.getAuthorities().stream()
                    .map(GrantedAuthority::getAuthority)
                    .map(a -> a.startsWith("ROLE_") ? a.substring(5) : a)
                    .collect(Collectors.toSet());

            // Set request context (ThreadLocal)
            RequestContext ctx = new RequestContext(tenantId, user.getId(), roles);
            RequestContextHolder.set(ctx);

            // Set PostgreSQL RLS context — matches Python's:
            //   SET LOCAL app.current_tenant = '<tenant_id>'
            entityManager.createNativeQuery("SELECT set_config('app.current_tenant', :tenant, true)")
                    .setParameter("tenant", tenantId)
                    .getSingleResult();

            log.debug("Tenant context set: tenant={}, user={}", tenantId, user.getId());

            filterChain.doFilter(request, response);
        } finally {
            RequestContextHolder.clear();
        }
    }

    /**
     * Resolves the active firm ID from the cookie or first active membership.
     * Matches Python's cookie-based tenant switch flow.
     */
    private String resolveActiveFirmId(HttpServletRequest request, String userId) {
        // 1. Check cookie
        if (request.getCookies() != null) {
            for (Cookie cookie : request.getCookies()) {
                if ("mesa_active_firm_id".equals(cookie.getName())) {
                    String firmId = cookie.getValue();
                    // Validate that user is actually a member of this firm
                    if (membershipRepository.existsByUserIdAndFirmIdAndActiveTrue(userId, firmId)) {
                        return firmId;
                    }
                    log.warn("Cookie references firm {} but user {} is not a member", firmId, userId);
                }
            }
        }

        // 2. Fallback to first active membership
        return membershipRepository.findFirstByUserIdAndActiveTrueOrderByCreatedAtAsc(userId)
                .map(Membership::getFirmId)
                .orElse(null);
    }
}
