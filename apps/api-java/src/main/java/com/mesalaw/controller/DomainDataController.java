package com.mesalaw.controller;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.matter.Claim;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Claim endpoints not covered by the matter summary routes.
 */
@RestController
@RequiredArgsConstructor
public class DomainDataController {

    private final EntityManager entityManager;

    // ── DTOs ──

    @Data
    @AllArgsConstructor
    public static class ClaimResponse {
        private String id, matterId, claimantPartyId, defendantPartyId;
        private String description, status, reviewStatus, sourceLocatorId;
    }

    @Data
    @AllArgsConstructor
    public static class ClaimEvidenceResponse {
        private String id, claim, evidence, support, confidence;
    }

    // ── Endpoints ──

    @GetMapping("/matters/{matterId}/claims")
    @SuppressWarnings("unchecked")
    public List<ClaimResponse> listClaims(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<Claim> claims = entityManager.createQuery(
                "SELECT c FROM Claim c WHERE c.matterId = :mid AND c.tenantId = :tid", Claim.class)
                .setParameter("mid", matterId).setParameter("tid", ctx.tenantId())
                .getResultList();

        return claims.stream().map(c -> new ClaimResponse(
                c.getId(), c.getMatterId(), c.getClaimantPartyId(), c.getDefendantPartyId(),
                c.getDescription(), c.getStatus(), c.getReviewStatus(), c.getSourceLocatorId()))
                .collect(Collectors.toList());
    }

}
