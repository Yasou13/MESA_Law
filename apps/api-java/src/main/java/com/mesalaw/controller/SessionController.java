package com.mesalaw.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.config.AppProperties;
import com.mesalaw.dto.SessionDto;
import com.mesalaw.entity.auth.Membership;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.MembershipRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;

/**
 * Session management endpoints (tenant switch, context info).
 * Replaces Python's routers/session.py.
 */
@RestController
@RequestMapping("/session")
@RequiredArgsConstructor
public class SessionController {

    private final MembershipRepository membershipRepository;
    private final AppProperties appProperties;

    /**
     * GET /session/context — Returns the resolved tenant/user context.
     * Matches Python: GET /session/context → getSessionContext
     */
    @GetMapping("/context")
    public SessionDto.ContextResponse getSessionContext() {
        RequestContext ctx = RequestContextHolder.get();
        return new SessionDto.ContextResponse(
                "success",
                ctx.tenantId(),
                ctx.principalId(),
                ctx.roles()
        );
    }

    /**
     * POST /session/active-firm — Switch the active tenant via secure cookie.
     * Matches Python: POST /session/active-firm → setActiveFirm
     */
    @PostMapping("/active-firm")
    public SessionDto.ActiveFirmResponse setActiveFirm(
            @RequestBody SessionDto.SetActiveFirmRequest request,
            HttpServletResponse response) {

        RequestContext ctx = RequestContextHolder.get();
        String firmId = request.getFirmId();

        Membership membership = membershipRepository
                .findByUserIdAndFirmId(ctx.principalId(), firmId)
                .filter(Membership::isActive)
                .orElseThrow(() -> new ProblemException(
                        403, "Forbidden", "User is not an active member of the requested firm"));

        // Set secure cookie — matches Python's response.set_cookie()
        Cookie cookie = new Cookie("mesa_active_firm_id", firmId);
        cookie.setHttpOnly(true);
        cookie.setSecure(appProperties.isSecureEnvironment());
        cookie.setPath("/");
        cookie.setMaxAge(-1); // Session cookie

        response.addCookie(cookie);

        return new SessionDto.ActiveFirmResponse(
                "success",
                firmId,
                membership.getRole().name()
        );
    }
}
