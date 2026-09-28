package com.mesalaw.entity.mesa;

import com.mesalaw.entity.base.TenantAwareEntity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Durable admission and mutation state for a MESA v4 write.
 * Replaces Python's {@code MesaSyncRecord} from models/mesa.py.
 */
@Entity
@Table(name = "mesa_sync_records", uniqueConstraints = {
        @UniqueConstraint(name = "uq_mesa_sync_idempotency", columnNames = {"tenant_id", "idempotency_key"})
})
@Getter
@Setter
@NoArgsConstructor
public class MesaSyncRecord extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "binding_id", nullable = false)
    private String bindingId;

    @Column(name = "source_locator_id")
    private String sourceLocatorId;

    @Column(name = "assertion_id")
    private String assertionId;

    @Column(name = "resource_type", nullable = false)
    private String resourceType;

    @Column(name = "resource_id", nullable = false)
    private String resourceId;

    @Column(name = "idempotency_key", nullable = false)
    private String idempotencyKey;

    @Column(name = "payload_hash", nullable = false, length = 64)
    private String payloadHash;

    @Column(name = "request_payload", nullable = false, columnDefinition = "jsonb")
    private String requestPayload;

    @Column(name = "mutation_id")
    private String mutationId;

    @Column(name = "candidate_id")
    private String candidateId;

    @Column(name = "pipeline_run_id")
    private String pipelineRunId;

    @Column(name = "session_id")
    private String sessionId;

    @Column(name = "status", nullable = false)
    private String status = "PENDING";

    @Column(name = "is_terminal", nullable = false)
    private boolean terminal = false;

    @Column(name = "attempts", nullable = false)
    private int attempts = 0;

    @Column(name = "last_error")
    private String lastError;

    @Column(name = "last_polled_at")
    private OffsetDateTime lastPolledAt;
}
