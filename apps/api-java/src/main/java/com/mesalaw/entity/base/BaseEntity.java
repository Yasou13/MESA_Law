package com.mesalaw.entity.base;

import java.time.OffsetDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import com.github.f4b6a3.uuid.UuidCreator;

import jakarta.persistence.Column;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Version;
import lombok.Getter;
import lombok.Setter;

/**
 * Base entity with audit fields, soft-delete, and legal hold.
 * Replaces Python's {@code AuditMixin} from core/models.py.
 *
 * <p>Every entity inherits:
 * <ul>
 *   <li>{@code id} — UUIDv7 (time-ordered) primary key</li>
 *   <li>{@code created_at / updated_at} — Audit timestamps</li>
 *   <li>{@code created_by / updated_by} — Who made the change</li>
 *   <li>{@code version_id} — Optimistic locking</li>
 *   <li>{@code is_deleted / deleted_at} — Soft delete</li>
 *   <li>{@code legal_hold} — Prevents deletion for legal reasons</li>
 * </ul>
 */
@MappedSuperclass
@Getter
@Setter
public abstract class BaseEntity {

    @Id
    @Column(name = "id", nullable = false, updatable = false, length = 36)
    private String id;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @Column(name = "created_by")
    private String createdBy;

    @Column(name = "updated_by")
    private String updatedBy;

    @Version
    @Column(name = "version_id", nullable = false)
    private Integer versionId = 1;

    @Column(name = "is_deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private OffsetDateTime deletedAt;

    @Column(name = "legal_hold", nullable = false)
    private boolean legalHold = false;

    /**
     * Auto-generates UUIDv7 before persist if not already set.
     * Matches Python's {@code default=generate_uuid} which uses uuid6.uuid7().
     */
    @PrePersist
    protected void prePersist() {
        if (this.id == null) {
            this.id = UuidCreator.getTimeOrderedEpoch().toString();
        }
    }
}
