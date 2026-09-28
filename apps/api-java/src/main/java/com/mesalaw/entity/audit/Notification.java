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
 * User notification with lifecycle tracking.
 * Replaces Python's {@code Notification} from models/audit.py.
 */
@Entity
@Table(name = "notifications")
@Getter
@Setter
@NoArgsConstructor
public class Notification extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "message", nullable = false)
    private String message;

    @Column(name = "category", nullable = false)
    private String category = "general";

    /** CREATED, DELIVERED, READ, ACKNOWLEDGED, ESCALATED, RESOLVED */
    @Column(name = "status", nullable = false)
    private String status = "CREATED";

    @Column(name = "timestamp", nullable = false)
    private OffsetDateTime timestamp;
}
