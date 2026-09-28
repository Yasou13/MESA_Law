package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Links a claim to supporting/refuting evidence.
 * Replaces Python's {@code ClaimEvidenceLink} from models/domain.py.
 */
@Entity
@Table(name = "claim_evidence_links")
@Getter
@Setter
@NoArgsConstructor
public class ClaimEvidenceLink extends TenantAwareEntity {

    @Column(name = "claim_id", nullable = false)
    private String claimId;

    @Column(name = "evidence_id", nullable = false)
    private String evidenceId;

    /** supports, refutes, partial */
    @Column(name = "support_type")
    private String supportType = "supports";
}
