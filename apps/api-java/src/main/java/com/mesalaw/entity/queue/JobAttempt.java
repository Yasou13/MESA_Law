package com.mesalaw.entity.queue;

import com.mesalaw.entity.base.BaseEntity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Individual attempt record for a background job.
 * Replaces Python's {@code JobAttempt} from models/queue.py.
 */
@Entity
@Table(name = "legal_job_attempts")
@Getter
@Setter
@NoArgsConstructor
public class JobAttempt extends BaseEntity {

    @Column(name = "job_id", nullable = false)
    private String jobId;

    @Column(name = "attempt_number", nullable = false)
    private int attemptNumber;

    @Column(name = "started_at")
    private OffsetDateTime startedAt;

    @Column(name = "finished_at")
    private OffsetDateTime finishedAt;

    @Column(name = "status", nullable = false)
    private String status;

    @Column(name = "error_details")
    private String errorDetails;

    @Column(name = "lease_token")
    private String leaseToken;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "job_id", insertable = false, updatable = false)
    private Job job;
}
