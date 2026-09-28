package com.mesalaw.entity.audit;

import com.mesalaw.entity.base.BaseEntity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Audit event for system-wide tracking.
 * Replaces Python's {@code AuditEvent} from models/audit.py.
 */
@Entity
@Table(name = "audit_events")
@Getter
@Setter
@NoArgsConstructor
public class AuditEvent extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "user_id")
    private String userId;

    @Column(name = "action", nullable = false)
    private String action;

    @Column(name = "entity_type", nullable = false)
    private String entityType;

    @Column(name = "entity_id", nullable = false)
    private String entityId;

    @Column(name = "changes", columnDefinition = "jsonb")
    private String changes;

    @Column(name = "timestamp", nullable = false)
    private OffsetDateTime timestamp;
}
