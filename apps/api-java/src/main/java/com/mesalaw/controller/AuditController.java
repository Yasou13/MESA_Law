package com.mesalaw.controller;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.audit.AuditEvent;
import com.mesalaw.repository.AuditEventRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Audit trail endpoints.
 * Replaces Python's routers/audit.py.
 */
@RestController
@RequestMapping("/audit")
@RequiredArgsConstructor
public class AuditController {

    private final AuditEventRepository auditEventRepository;

    @Data @AllArgsConstructor
    public static class AuditEventResponse {
        private String id, userId, action, entityType, entityId;
        private String changes;
        private String timestamp;
    }

    /**
     * GET /audit/events — List audit events.
     * Matches Python: GET /audit/events → listAuditEvents
     */
    @GetMapping("/events")
    public List<AuditEventResponse> listAuditEvents(
            @RequestParam(defaultValue = "100") int limit) {
        RequestContext ctx = RequestContextHolder.get();

        // Use repository with default ordering
        List<AuditEvent> events = auditEventRepository
                .findByTenantIdOrderByTimestampDesc(ctx.tenantId());

        return events.stream()
                .limit(limit)
                .map(e -> new AuditEventResponse(
                        e.getId(), e.getUserId(), e.getAction(),
                        e.getEntityType(), e.getEntityId(),
                        e.getChanges(),
                        e.getTimestamp().toString()))
                .collect(Collectors.toList());
    }
}
