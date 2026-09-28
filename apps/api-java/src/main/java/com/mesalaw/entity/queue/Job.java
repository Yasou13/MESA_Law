package com.mesalaw.entity.queue;

import com.mesalaw.entity.base.BaseEntity;

import java.time.OffsetDateTime;
import java.util.List;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Background processing job (document scan, parse, OCR, extraction, sync).
 * Replaces Python's {@code Job} from models/queue.py.
 */
@Entity
@Table(name = "legal_jobs")
@Getter
@Setter
@NoArgsConstructor
public class Job extends BaseEntity {

    @Column(name = "type", nullable = false)
    private String type;

    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private String payload;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private JobStatus status = JobStatus.PENDING;

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "matter_id")
    private String matterId;

    @Column(name = "max_retries", nullable = false)
    private int maxRetries = 3;

    @Column(name = "retries", nullable = false)
    private int retries = 3;

    @Column(name = "attempts_made", nullable = false)
    private int attemptsMade = 0;

    @Column(name = "run_at")
    private OffsetDateTime runAt;

    @Column(name = "locked_at")
    private OffsetDateTime lockedAt;

    @Column(name = "locked_until")
    private OffsetDateTime lockedUntil;

    @Column(name = "heartbeat_at")
    private OffsetDateTime heartbeatAt;

    @Column(name = "lease_token")
    private String leaseToken;

    @Column(name = "requested_by")
    private String requestedBy;

    @Column(name = "idempotency_key")
    private String idempotencyKey;

    @Column(name = "error_message")
    private String errorMessage;

    @Column(name = "error_class")
    private String errorClass;

    @OneToMany(mappedBy = "job", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<JobAttempt> attempts;
}
