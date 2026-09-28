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
 * Stable binding between a MESA Law matter and MESA Core v4 catalog entities.
 * Replaces Python's {@code MesaScopeBinding} from models/mesa.py.
 */
@Entity
@Table(name = "mesa_scope_bindings", uniqueConstraints = {
        @UniqueConstraint(name = "uq_mesa_binding_matter", columnNames = {"tenant_id", "matter_id"}),
        @UniqueConstraint(name = "uq_mesa_binding_dataset", columnNames = {"tenant_id", "dataset_id"})
})
@Getter
@Setter
@NoArgsConstructor
public class MesaScopeBinding extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "mesa_tenant_id", nullable = false)
    private String mesaTenantId;

    @Column(name = "workspace_id", nullable = false)
    private String workspaceId;

    @Column(name = "dataset_id", nullable = false)
    private String datasetId;

    @Column(name = "agent_id", nullable = false)
    private String agentId;

    @Column(name = "provisioning_status", nullable = false)
    private String provisioningStatus = "PENDING";

    @Column(name = "last_verified_at")
    private OffsetDateTime lastVerifiedAt;

    @Column(name = "last_error")
    private String lastError;
}
