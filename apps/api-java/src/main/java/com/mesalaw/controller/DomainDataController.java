package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.matter.Claim;
import com.mesalaw.entity.matter.EvidenceItem;
import com.mesalaw.entity.matter.MatterEvent;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Domain data endpoints — claims, evidence, timeline, claim-evidence links.
 * Replaces Python's routers/domain_data.py.
 */
@RestController
@RequiredArgsConstructor
public class DomainDataController {

    private final EntityManager entityManager;

    // ── DTOs ──

    @Data @AllArgsConstructor
    public static class ClaimResponse {
        private String id, matterId, claimantPartyId, defendantPartyId;
        private String description, status, reviewStatus, sourceLocatorId;
    }

    @Data @AllArgsConstructor
    public static class EvidenceResponse {
        private String id, matterId, documentId, description, reviewStatus, sourceLocatorId;
    }

    @Data @AllArgsConstructor
    public static class TimelineEventResponse {
        private String id, date, title, description, source, confidence;
    }

    @Data @AllArgsConstructor
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
                c.getDescription(), c.getStatus(), c.getReviewStatus(), c.getSourceLocatorId()
        )).collect(Collectors.toList());
    }

    @GetMapping("/matters/{matterId}/evidence")
    public List<EvidenceResponse> listEvidence(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<EvidenceItem> items = entityManager.createQuery(
                "SELECT e FROM EvidenceItem e WHERE e.matterId = :mid AND e.tenantId = :tid", EvidenceItem.class)
                .setParameter("mid", matterId).setParameter("tid", ctx.tenantId())
                .getResultList();

        return items.stream().map(e -> new EvidenceResponse(
                e.getId(), e.getMatterId(), e.getDocumentId(),
                e.getDescription(), e.getReviewStatus(), e.getSourceLocatorId()
        )).collect(Collectors.toList());
    }

    @GetMapping("/matters/{matterId}/timeline")
    public List<TimelineEventResponse> listTimeline(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<MatterEvent> events = entityManager.createQuery(
                "SELECT e FROM MatterEvent e WHERE e.matterId = :mid AND e.tenantId = :tid ORDER BY e.eventDate DESC",
                MatterEvent.class)
                .setParameter("mid", matterId).setParameter("tid", ctx.tenantId())
                .getResultList();

        return events.stream().map(e -> new TimelineEventResponse(
                "event_" + e.getId(),
                e.getEventDate().toString(),
                e.getEventType(),
                e.getDescription(),
                e.getSourceType(),
                e.getConfidence()
        )).collect(Collectors.toList());
    }
}
