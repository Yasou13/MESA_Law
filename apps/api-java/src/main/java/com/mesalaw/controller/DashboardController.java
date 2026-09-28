package com.mesalaw.controller;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Dashboard aggregated metrics endpoint.
 * Replaces Python's routers/dashboard.py.
 */
@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final EntityManager entityManager;

    @Data @AllArgsConstructor
    public static class DashboardMetrics {
        private long activeMatters;
        private long pendingReviews;
        private long upcomingDeadlines;
        private long unreadNotifications;
        private long failedOperations;
        private List<String> degradedCapabilities;
        private String systemStatus;
    }

    /**
     * GET /api/v1/dashboard/metrics — Aggregated dashboard stats.
     * Matches Python: GET /api/v1/dashboard/metrics → getDashboardMetrics
     */
    @GetMapping("/metrics")
    public DashboardMetrics getMetrics() {
        RequestContext ctx = RequestContextHolder.get();
        String tid = ctx.tenantId();

        long activeMatters = count("SELECT COUNT(m) FROM Matter m WHERE m.tenantId = :tid AND m.status = 'open'", tid);
        long pendingReviews = count("SELECT COUNT(r) FROM ReviewItem r WHERE r.tenantId = :tid AND r.status = 'PROPOSED'", tid);
        long upcomingDeadlines = count("SELECT COUNT(d) FROM ApprovedDeadline d WHERE d.tenantId = :tid AND d.completed = false", tid);
        long unreadNotifications = count("SELECT COUNT(n) FROM Notification n WHERE n.tenantId = :tid AND n.userId = :uid AND n.status = 'CREATED'",
                tid, ctx.principalId());
        long failedOps = count("SELECT COUNT(j) FROM Job j WHERE j.tenantId = :tid AND j.status IN ('FAILED', 'DEAD')", tid);

        List<String> degraded = new ArrayList<>();
        // TODO: Check Redis, MinIO, ClamAV connectivity
        String status = degraded.isEmpty() ? "ok" : "degraded";

        return new DashboardMetrics(activeMatters, pendingReviews, upcomingDeadlines,
                unreadNotifications, failedOps, degraded, status);
    }

    private long count(String jpql, String tenantId) {
        return (long) entityManager.createQuery(jpql)
                .setParameter("tid", tenantId)
                .getSingleResult();
    }

    private long count(String jpql, String tenantId, String userId) {
        return (long) entityManager.createQuery(jpql)
                .setParameter("tid", tenantId)
                .setParameter("uid", userId)
                .getSingleResult();
    }
}
