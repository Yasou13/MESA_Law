package com.mesalaw.controller;

import java.util.List;

import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.DomainDataDto;
import com.mesalaw.repository.ClaimRepository;
import com.mesalaw.security.MatterAccessGuard;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import lombok.RequiredArgsConstructor;

/**
 * Claim endpoints not covered by the matter summary routes.
 * Replaces Python's routers/domain_data.py (evidence, timeline and claims-evidence live in MatterController).
 */
@RestController
@RequiredArgsConstructor
public class DomainDataController {

    private final ClaimRepository claimRepository;
    private final MatterAccessGuard accessGuard;

    // ── Endpoints ──

    /**
     * GET /matters/{matterId}/claims — List claims for a matter.
     * Matches Python: GET /matters/{matter_id}/claims → listClaims
     */
    @GetMapping("/matters/{matterId}/claims")
    @Transactional(readOnly = true)
    public List<DomainDataDto.ClaimResponse> listClaims(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        accessGuard.canRead(ctx, matterId);

        return claimRepository.findByMatterIdAndTenantIdAndDeletedFalse(matterId, ctx.tenantId())
                .stream()
                .map(DomainDataDto.ClaimResponse::from)
                .toList();
    }
}
