package com.mesalaw.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.deadline.ApprovedDeadline;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.ApprovedDeadlineRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Deadline management endpoints.
 * Replaces Python's routers/deadlines.py.
 */
@RestController
@RequestMapping("/deadlines")
@RequiredArgsConstructor
public class DeadlineController {

    private final ApprovedDeadlineRepository approvedDeadlineRepository;

    @Data
    @AllArgsConstructor
    public static class DeadlineResponse {
        private String id;
        private String matterId;
        private String dueDate;
        private String description;
        private boolean completed;
    }

    /**
     * GET /deadlines — List active deadlines, optionally filtered by matter.
     * Matches Python: GET /deadlines → listDeadlines
     */
    @GetMapping
    public List<DeadlineResponse> listDeadlines(@RequestParam(required = false) String matterId) {
        RequestContext ctx = RequestContextHolder.get();

        List<ApprovedDeadline> deadlines;
        if (matterId != null) {
            deadlines = approvedDeadlineRepository
                    .findByMatterIdAndCompletedFalseOrderByDueDateAsc(matterId);
        } else {
            deadlines = approvedDeadlineRepository
                    .findByTenantIdAndCompletedFalseOrderByDueDateAsc(ctx.tenantId());
        }

        return deadlines.stream()
                .map(d -> new DeadlineResponse(
                        d.getId(),
                        d.getMatterId(),
                        d.getDueDate().toString(),
                        d.getDescription(),
                        d.isCompleted()))
                .collect(Collectors.toList());
    }

    /**
     * POST /deadlines/{deadlineId}/complete — Mark a deadline as completed.
     * Matches Python: POST /deadlines/{deadline_id}/complete → completeDeadline
     */
    @PostMapping("/{deadlineId}/complete")
    public Map<String, String> completeDeadline(@PathVariable String deadlineId) {
        RequestContext ctx = RequestContextHolder.get();

        ApprovedDeadline deadline = approvedDeadlineRepository.findById(deadlineId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Deadline not found"));

        if (!deadline.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Deadline not found");
        }

        deadline.setCompleted(true);
        approvedDeadlineRepository.save(deadline);

        return Map.of("status", "success");
    }
}
