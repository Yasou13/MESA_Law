package com.mesalaw.controller;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.config.AppProperties;
import com.mesalaw.entity.document.Document;
import com.mesalaw.entity.queue.Job;
import com.mesalaw.entity.research.LegalSource;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Legal research endpoints — start research job, search sources.
 * Replaces Python's routers/research.py.
 */
@RestController
@RequestMapping("/research")
@RequiredArgsConstructor
public class ResearchController {

    private final EntityManager entityManager;
    private final AppProperties appProperties;

    @Data
    public static class ResearchRequest {
        @NotBlank private String matterId;
        @NotBlank private String query;
    }

    @Data @AllArgsConstructor
    public static class ResearchJobResponse {
        private String status;
        private String jobId;
    }

    @Data @AllArgsConstructor
    public static class LegalSourceResponse {
        private String id, title, citation, sourceType, content;
    }

    /**
     * POST /research/start — Start a legal research background job.
     * Matches Python: POST /research/start → startLegalResearch
     */
    @PostMapping("/start")
    public ResearchJobResponse startResearch(@Valid @RequestBody ResearchRequest request) {
        if (!appProperties.isExternalResearchEnabled()) {
            throw new ProblemException(501, "Not Implemented", "External legal research is disabled in the MVP");
        }

        RequestContext ctx = RequestContextHolder.get();

        Job job = new Job();
        job.setType("PERFORM_LEGAL_RESEARCH");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(request.getMatterId());
        job.setRequestedBy(ctx.principalId());
        job.setPayload("{\"matter_id\":\"" + request.getMatterId()
                + "\",\"query\":\"" + request.getQuery()
                + "\",\"tenant_id\":\"" + ctx.tenantId() + "\"}");
        entityManager.persist(job);
        entityManager.flush();

        return new ResearchJobResponse("accepted", job.getId());
    }

    /**
     * GET /research/search — Search legal sources + internal documents.
     * Matches Python: GET /research/search → searchLegalResearch
     */
    @GetMapping("/search")
    public List<LegalSourceResponse> searchSources(@RequestParam String q) {
        if (!appProperties.isExternalResearchEnabled()) {
            throw new ProblemException(501, "Not Implemented", "External legal research is disabled in the MVP");
        }

        RequestContext ctx = RequestContextHolder.get();
        List<LegalSourceResponse> results = new ArrayList<>();

        // 1. Search external legal sources
        List<LegalSource> sources = entityManager.createQuery(
                "SELECT s FROM LegalSource s WHERE LOWER(s.title) LIKE :q OR LOWER(s.content) LIKE :q OR LOWER(s.citation) LIKE :q",
                LegalSource.class)
                .setParameter("q", "%" + q.toLowerCase() + "%")
                .setMaxResults(10)
                .getResultList();

        sources.forEach(s -> results.add(new LegalSourceResponse(
                s.getId(), s.getTitle(), s.getCitation(), s.getSourceType(),
                s.getContent().length() > 500 ? s.getContent().substring(0, 500) + "..." : s.getContent())));

        // 2. Search internal firm documents
        List<Document> internalDocs = entityManager.createQuery(
                "SELECT d FROM Document d WHERE d.tenantId = :tid AND LOWER(d.title) LIKE :q",
                Document.class)
                .setParameter("tid", ctx.tenantId())
                .setParameter("q", "%" + q.toLowerCase() + "%")
                .setMaxResults(10)
                .getResultList();

        internalDocs.forEach(d -> results.add(new LegalSourceResponse(
                d.getId(), d.getTitle(),
                "Internal Doc: " + d.getId().substring(0, 8),
                "internal_precedent",
                "Internal document uploaded to matter " + d.getMatterId() + ". Title: " + d.getTitle())));

        return results;
    }
}
