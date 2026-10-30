package com.mesalaw.security;

import java.util.Set;

import org.springframework.stereotype.Component;

import com.mesalaw.entity.matter.MatterMember;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.MatterMemberRepository;

import lombok.RequiredArgsConstructor;

/**
 * Role + matter-membership checks.
 * Java equivalent of Python's {@code BasePolicy._enforce} / {@code _enforce_matter} in core/policies.py.
 */
@Component
@RequiredArgsConstructor
public class MatterAccessGuard {

    /** MatterAccessPolicy.can_read / can_list. */
    public static final Set<String> READ_ROLES = Set.of(
            "FIRM_ADMIN", "ATTORNEY", "PARALEGAL", "READ_ONLY", "AUDITOR");
    /** MatterAccessPolicy.can_write, DeadlineAccessPolicy.can_manage. */
    public static final Set<String> WRITE_ROLES = Set.of("FIRM_ADMIN", "ATTORNEY", "PARALEGAL");
    /** ReviewAccessPolicy.can_approve. */
    public static final Set<String> REVIEW_DECISION_ROLES = Set.of("FIRM_ADMIN", "ATTORNEY");

    public static final Set<String> READ_SCOPES = Set.of("read", "write", "admin");
    public static final Set<String> WRITE_SCOPES = Set.of("write", "admin");

    private final MatterMemberRepository matterMemberRepository;

    public void requireRoles(RequestContext ctx, Set<String> roles, String action) {
        if (!ctx.hasAnyRole(roles)) {
            throw new ProblemException(403, "Forbidden", "Requires one of scopes: " + action);
        }
    }

    public void requireMatterScope(RequestContext ctx, String matterId, Set<String> scopes) {
        MatterMember member = matterMemberRepository
                .findByMatterIdAndUserIdAndTenantIdAndDeletedFalse(matterId, ctx.principalId(), ctx.tenantId())
                .orElseThrow(() -> new ProblemException(403, "Forbidden", "You are not a member of this matter"));
        if (!scopes.contains(member.getAccessScope())) {
            throw new ProblemException(403, "Forbidden", "Insufficient matter access scope");
        }
    }

    /** MatterAccessPolicy.can_read. */
    public void canRead(RequestContext ctx, String matterId) {
        requireRoles(ctx, READ_ROLES, "read matters");
        requireMatterScope(ctx, matterId, READ_SCOPES);
    }

    /** MatterAccessPolicy.can_write. */
    public void canWrite(RequestContext ctx, String matterId) {
        requireRoles(ctx, WRITE_ROLES, "write matters");
        requireMatterScope(ctx, matterId, WRITE_SCOPES);
    }
}
