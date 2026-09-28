package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.queue.Job;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Operations monitoring endpoints — jobs list and operational metrics.
 * Replaces Python's routers/operations.py.
 */
@RestController
@RequestMapping("/operations")
@RequiredArgsConstructor
public class OperationsController {

    private final EntityManager entityManager;

    @Data @AllArgsConstructor
    public static class JobResponse {
        private String id, type, status, tenantId, matterId;
        private OffsetDateTime createdAt, updatedAt;
        private String errorMessage;
        private int retries, maxRetries;
        private String payload;
    }

    @Data @AllArgsConstructor
    public static class OperationalMetrics {
        private long jobQueueDepth;
        private long staleJobLeases;
        private long documentPipelineFailures;
        private long reviewBacklog;
        private Map<String, Long> mesaMutationTerminalStatuses;
    }

    /**
     * GET /operations/jobs — List background worker jobs.
     * Matches Python: GET /operations/jobs → listJobs
     */
    @GetMapping("/jobs")
    public List<JobResponse> listJobs(@RequestParam(defaultValue = "100") int limit) {
        RequestContext ctx = RequestContextHolder.get();
        List<Job> jobs = entityManager.createQuery(
                "SELECT j FROM Job j WHERE j.tenantId = :tid ORDER BY j.createdAt DESC", Job.class)
                .setParameter("tid", ctx.tenantId())
                .setMaxResults(limit)
                .getResultList();

        return jobs.stream().map(j -> new JobResponse(
                j.getId(), j.getType(), j.getStatus().name(),
                j.getTenantId(), j.getMatterId(),
                j.getCreatedAt(), j.getUpdatedAt(),
                j.getErrorMessage(), j.getRetries(), j.getMaxRetries(),
                j.getPayload()
        )).collect(Collectors.toList());
    }

    /**
     * GET /operations/metrics — Operational metrics snapshot.
     * Matches Python: GET /operations/metrics → getOperationalMetrics
     */
    @GetMapping("/metrics")
    public OperationalMetrics getOperationalMetrics() {
        RequestContext ctx = RequestContextHolder.get();
        String tid = ctx.tenantId();

        long queueDepth = count(
                "SELECT COUNT(j) FROM Job j WHERE j.tenantId = :tid AND j.status IN ('PENDING','RUNNING')", tid);
        long staleLeases = count(
                "SELECT COUNT(j) FROM Job j WHERE j.tenantId = :tid AND j.status = 'RUNNING' AND j.lockedUntil < :now", tid);
        long pipelineFailures = count(
                "SELECT COUNT(j) FROM Job j WHERE j.tenantId = :tid AND j.type IN ('SCAN_DOCUMENT','PARSE_DOCUMENT','OCR_DOCUMENT','EXTRACT_LEGAL_DATA') AND j.status IN ('FAILED','DEAD')", tid);
        long reviewBacklog = count(
                "SELECT COUNT(r) FROM ReviewItem r WHERE r.tenantId = :tid AND r.status = 'PROPOSED'", tid);

        // MESA mutation terminal statuses
        @SuppressWarnings("unchecked")
        List<Object[]> mutationRows = entityManager.createQuery(
                "SELECT m.status, COUNT(m) FROM MesaSyncRecord m WHERE m.tenantId = :tid AND m.terminal = true GROUP BY m.status")
                .setParameter("tid", tid)
                .getResultList();

        Map<String, Long> mesaStatuses = new HashMap<>();
        for (Object[] row : mutationRows) {
            mesaStatuses.put((String) row[0], (Long) row[1]);
        }

        return new OperationalMetrics(queueDepth, staleLeases, pipelineFailures, reviewBacklog, mesaStatuses);
    }

    private long count(String jpql, String tenantId) {
        var query = entityManager.createQuery(jpql);
        query.setParameter("tid", tenantId);
        if (jpql.contains(":now")) {
            query.setParameter("now", OffsetDateTime.now());
        }
        return (long) query.getSingleResult();
    }
}
