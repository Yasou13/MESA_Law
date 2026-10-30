package com.mesalaw.controller;

import java.util.List;

import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.DeadlineDto;
import com.mesalaw.entity.deadline.ApprovedDeadline;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.ApprovedDeadlineRepository;
import com.mesalaw.security.MatterAccessGuard;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

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
    private final MatterAccessGuard accessGuard;

    /**
     * GET /deadlines — List active deadlines, optionally filtered by matter.
     * Matches Python: GET /deadlines → listDeadlines
     */
    @GetMapping
    @Transactional(readOnly = true)
    public List<DeadlineDto.Response> listDeadlines(@RequestParam(required = false) String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<ApprovedDeadline> deadlines;
        if (matterId != null) {
            accessGuard.canRead(ctx, matterId);
            deadlines = approvedDeadlineRepository
                    .findByTenantIdAndMatterIdAndCompletedFalseOrderByDueDateAsc(ctx.tenantId(), matterId);
        } else {
            accessGuard.requireRoles(ctx, MatterAccessGuard.READ_ROLES, "list assigned matters");
            deadlines = approvedDeadlineRepository.findOpenForMember(ctx.tenantId(), ctx.principalId());
        }

        return deadlines.stream().map(DeadlineDto.Response::from).toList();
    }

    /**
     * POST /deadlines/{deadlineId}/complete — Mark a deadline as completed.
     * Matches Python: POST /deadlines/{deadline_id}/complete → completeDeadline
     */
    @PostMapping("/{deadlineId}/complete")
    @Transactional
    public DeadlineDto.CompleteResponse completeDeadline(@PathVariable String deadlineId) {
        RequestContext ctx = RequestContextHolder.get();

        ApprovedDeadline deadline = approvedDeadlineRepository.findByIdAndTenantId(deadlineId, ctx.tenantId())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Deadline not found"));

        // Python: DeadlineAccessPolicy.can_manage + MatterAccessPolicy.can_write
        accessGuard.canWrite(ctx, deadline.getMatterId());

        deadline.setCompleted(true);
        deadline.setUpdatedBy(ctx.principalId());
        approvedDeadlineRepository.save(deadline);

        return new DeadlineDto.CompleteResponse("success");
    }
}
