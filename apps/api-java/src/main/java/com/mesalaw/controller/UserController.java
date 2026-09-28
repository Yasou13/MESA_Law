package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.auth.User;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.UserRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * User profile endpoints.
 * Replaces Python's routers/users.py.
 */
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

    private final UserRepository userRepository;

    @Data @AllArgsConstructor
    public static class UserProfileResponse {
        private String id, email, fullName;
        private Set<String> roles;
        private boolean supportAccessGranted;
        private OffsetDateTime supportAccessGrantedUntil;
    }

    @Data
    public static class UpdateProfileRequest {
        @Size(min = 1, max = 255) private String fullName;
        @Size(min = 3, max = 255) private String email;
    }

    @Data
    public static class SupportAccessRequest {
        @Min(1) @Max(72) private int durationHours = 24;
    }

    /**
     * GET /users/me — Current user profile.
     * Matches Python: GET /users/me → getCurrentUserProfile
     */
    @GetMapping("/me")
    public UserProfileResponse getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Jwt jwt = (Jwt) auth.getPrincipal();
        String keycloakId = jwt.getSubject();

        User user = userRepository.findByKeycloakId(keycloakId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "User not found"));

        Set<String> roles = auth.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .map(a -> a.startsWith("ROLE_") ? a.substring(5) : a)
                .collect(Collectors.toSet());

        return new UserProfileResponse(
                user.getId(), user.getEmail(), user.getFullName(),
                roles, user.isSupportAccessGranted(), user.getSupportAccessGrantedUntil());
    }

    /**
     * PUT /users/me — Update current user profile.
     * Matches Python: PUT /users/me → updateCurrentUserProfile
     */
    @PutMapping("/me")
    public UserProfileResponse updateProfile(@Valid @RequestBody UpdateProfileRequest request) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Jwt jwt = (Jwt) auth.getPrincipal();

        User user = userRepository.findByKeycloakId(jwt.getSubject())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "User not found"));

        if (request.getFullName() != null) user.setFullName(request.getFullName());
        if (request.getEmail() != null) user.setEmail(request.getEmail());
        userRepository.save(user);

        Set<String> roles = auth.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .map(a -> a.startsWith("ROLE_") ? a.substring(5) : a)
                .collect(Collectors.toSet());

        return new UserProfileResponse(
                user.getId(), user.getEmail(), user.getFullName(),
                roles, user.isSupportAccessGranted(), user.getSupportAccessGrantedUntil());
    }

    /**
     * POST /users/me/support-access — Grant temporary support access.
     * Matches Python: POST /users/me/support-access → grantSupportAccess
     */
    @PostMapping("/me/support-access")
    public java.util.Map<String, Object> grantSupportAccess(@Valid @RequestBody SupportAccessRequest request) {
        RequestContext ctx = RequestContextHolder.get();
        if (!ctx.hasRole("FIRM_ADMIN")) {
            throw new ProblemException(403, "Forbidden", "Only FIRM_ADMIN can grant support access");
        }

        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        Jwt jwt = (Jwt) auth.getPrincipal();

        User user = userRepository.findByKeycloakId(jwt.getSubject())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "User not found"));

        user.setSupportAccessGranted(true);
        user.setSupportAccessGrantedUntil(OffsetDateTime.now().plusHours(request.getDurationHours()));
        userRepository.save(user);

        return java.util.Map.of(
                "status", "granted",
                "is_support_access_granted", true,
                "support_access_granted_until", user.getSupportAccessGrantedUntil().toString());
    }
}
