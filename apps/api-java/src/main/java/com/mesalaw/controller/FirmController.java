package com.mesalaw.controller;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.FirmDto;
import com.mesalaw.entity.auth.Firm;
import com.mesalaw.entity.auth.Membership;
import com.mesalaw.entity.auth.Role;
import com.mesalaw.entity.auth.User;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.FirmRepository;
import com.mesalaw.repository.MembershipRepository;
import com.mesalaw.repository.UserRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * Firm management endpoints.
 * Replaces Python's routers/firms.py (all 4 endpoints).
 */
@RestController
@RequestMapping("/firms")
@RequiredArgsConstructor
public class FirmController {

    private final FirmRepository firmRepository;
    private final UserRepository userRepository;
    private final MembershipRepository membershipRepository;

    /**
     * GET /firms — List firms the authenticated user belongs to.
     * Matches Python: GET /firms → listUserFirms
     */
    @GetMapping
    public List<FirmDto.Response> listUserFirms() {
        RequestContext ctx = RequestContextHolder.get();
        List<Membership> memberships = membershipRepository.findByUserIdAndActiveTrue(ctx.principalId());

        return memberships.stream()
                .map(m -> firmRepository.findById(m.getFirmId()).orElse(null))
                .filter(f -> f != null)
                .map(f -> new FirmDto.Response(f.getId(), f.getName()))
                .collect(Collectors.toList());
    }

    /**
     * GET /firms/members — List members of the current tenant's firm.
     * Matches Python: GET /firms/members → listFirmMembers
     */
    @GetMapping("/members")
    public List<FirmDto.MemberResponse> listFirmMembers() {
        RequestContext ctx = RequestContextHolder.get();
        List<Membership> memberships = membershipRepository.findByFirmId(ctx.tenantId());

        return memberships.stream()
                .map(m -> {
                    User user = userRepository.findById(m.getUserId()).orElse(null);
                    if (user == null) return null;
                    return new FirmDto.MemberResponse(
                            user.getId(),
                            user.getEmail(),
                            user.getFullName(),
                            m.getRole().name(),
                            m.isActive()
                    );
                })
                .filter(r -> r != null)
                .collect(Collectors.toList());
    }

    /**
     * GET /firms/{firmId} — Get firm details.
     * Matches Python: GET /firms/{firm_id} → getFirmDetails
     */
    @GetMapping("/{firmId}")
    public FirmDto.Response getFirmDetails(@PathVariable String firmId) {
        RequestContext ctx = RequestContextHolder.get();

        if (!ctx.tenantId().equals(firmId) && !ctx.hasRole("FIRM_ADMIN")) {
            throw new ProblemException(403, "Forbidden", "Access denied to requested firm details");
        }

        Firm firm = firmRepository.findById(firmId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Firm not found"));

        return new FirmDto.Response(firm.getId(), firm.getName());
    }

    /**
     * POST /firms — Create a new firm. The creator becomes FIRM_ADMIN.
     * Matches Python: POST /firms → createFirm
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public FirmDto.Response createFirm(@Valid @RequestBody FirmDto.CreateRequest request) {
        RequestContext ctx = RequestContextHolder.get();

        Firm firm = new Firm();
        firm.setName(request.getName());
        firmRepository.save(firm);

        Membership membership = new Membership();
        membership.setUserId(ctx.principalId());
        membership.setFirmId(firm.getId());
        membership.setRole(Role.FIRM_ADMIN);
        membership.setActive(true);
        membershipRepository.save(membership);

        return new FirmDto.Response(firm.getId(), firm.getName());
    }

    /**
     * PUT /firms/{firmId}/members/{userId}/role — Change a member's role.
     * Matches Python: PUT /firms/{firm_id}/members/{user_id}/role → elevateRole
     */
    @PutMapping("/{firmId}/members/{userId}/role")
    public java.util.Map<String, String> elevateRole(
            @PathVariable String firmId,
            @PathVariable String userId,
            @Valid @RequestBody FirmDto.RoleElevationRequest request) {

        RequestContext ctx = RequestContextHolder.get();

        if (!ctx.hasRole("FIRM_ADMIN")) {
            throw new ProblemException(403, "Forbidden", "Only FIRM_ADMIN can manage roles");
        }
        if (!ctx.tenantId().equals(firmId)) {
            throw new ProblemException(403, "Forbidden", "Cross-tenant access forbidden");
        }

        Membership membership = membershipRepository.findByUserIdAndFirmId(userId, firmId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Membership not found"));

        membership.setRole(Role.valueOf(request.getRole()));
        membershipRepository.save(membership);

        return java.util.Map.of("status", "success", "new_role", membership.getRole().name());
    }
}
