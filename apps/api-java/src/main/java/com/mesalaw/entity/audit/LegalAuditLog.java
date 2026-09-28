package com.mesalaw.entity.audit;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Immutable audit trail for legal state changes (approve, reject, correct).
 * Replaces Python's {@code AuditLog} from models/review.py.
 */
@Entity
@Table(name = "legal_audit_logs")
@Getter
@Setter
@NoArgsConstructor
public class LegalAuditLog extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "matter_id")
    private String matterId;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "action", nullable = false)
    private String action;

    @Column(name = "entity_type", nullable = false)
    private String entityType;

    @Column(name = "entity_id", nullable = false)
    private String entityId;

    @Column(name = "details", nullable = false, columnDefinition = "jsonb")
    private String details;

    @Column(name = "ip_address")
    private String ipAddress;
}
