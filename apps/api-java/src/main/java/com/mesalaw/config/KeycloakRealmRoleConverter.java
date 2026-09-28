package com.mesalaw.config;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.core.convert.converter.Converter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;

/**
 * Extracts Keycloak realm_access.roles from JWT claims and converts them to
 * Spring Security GrantedAuthority objects.
 *
 * <p>Keycloak JWT structure:
 * <pre>
 * {
 *   "realm_access": {
 *     "roles": ["FIRM_ADMIN", "ATTORNEY", ...]
 *   }
 * }
 * </pre>
 *
 * <p>This replaces the Python code in auth.py:
 * <pre>
 * realm_access = payload.get("realm_access", {})
 * roles = realm_access.get("roles", [])
 * </pre>
 */
public class KeycloakRealmRoleConverter implements Converter<Jwt, Collection<GrantedAuthority>> {

    private static final String ROLE_PREFIX = "ROLE_";

    @Override
    @SuppressWarnings("unchecked")
    public Collection<GrantedAuthority> convert(Jwt jwt) {
        Map<String, Object> realmAccess = jwt.getClaimAsMap("realm_access");
        if (realmAccess == null || !realmAccess.containsKey("roles")) {
            return Collections.emptyList();
        }

        Object rolesObj = realmAccess.get("roles");
        if (!(rolesObj instanceof List<?>)) {
            return Collections.emptyList();
        }

        List<String> roles = (List<String>) rolesObj;
        return roles.stream()
                .map(role -> new SimpleGrantedAuthority(ROLE_PREFIX + role))
                .collect(Collectors.toList());
    }
}
