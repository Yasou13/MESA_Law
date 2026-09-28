package com.mesalaw.entity.base;

import com.mesalaw.entity.auth.Firm;

import jakarta.persistence.Column;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;
import lombok.Setter;

/**
 * Base entity for all tenant-scoped tables. Adds a {@code tenant_id} FK to the firms table.
 * Replaces Python's {@code TenantAwareMixin} from core/models.py.
 *
 * <p>Combined with PostgreSQL Row-Level Security (RLS), this ensures that
 * each query is automatically filtered by the current tenant context.</p>
 */
@MappedSuperclass
@Getter
@Setter
public abstract class TenantAwareEntity extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tenant_id", insertable = false, updatable = false)
    private Firm tenant;
}
