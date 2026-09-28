package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A piece of evidence supporting or refuting a claim.
 * Replaces Python's {@code EvidenceItem} from models/domain.py.
 */
@Entity
@Table(name = "evidence_items")
@Getter
@Setter
@NoArgsConstructor
public class EvidenceItem extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "document_id")
    private String documentId;

    @Column(name = "description", nullable = false)
    private String description;

    @Column(name = "review_status", nullable = false)
    private String reviewStatus = "approved";

    @Column(name = "source_locator_id")
    private String sourceLocatorId;
}
