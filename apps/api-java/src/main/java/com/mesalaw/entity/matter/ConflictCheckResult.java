package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Result of a conflict of interest check before opening a matter.
 * Replaces Python's {@code ConflictCheckResult} from models/domain.py.
 */
@Entity
@Table(name = "conflict_checks")
@Getter
@Setter
@NoArgsConstructor
public class ConflictCheckResult extends TenantAwareEntity {

    @Column(name = "matter_id")
    private String matterId;

    @Column(name = "requested_by", nullable = false)
    private String requestedBy;

    @Column(name = "party_names", nullable = false, columnDefinition = "jsonb")
    private String partyNames;

    @Column(name = "has_conflicts", nullable = false)
    private boolean hasConflicts = false;

    @Column(name = "results", nullable = false, columnDefinition = "jsonb")
    private String results;

    @Column(name = "status", nullable = false)
    private String status = "completed";
}
