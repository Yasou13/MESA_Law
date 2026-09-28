package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A legal claim made by one party against another.
 * Replaces Python's {@code Claim} from models/domain.py.
 */
@Entity
@Table(name = "claims")
@Getter
@Setter
@NoArgsConstructor
public class Claim extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "claimant_party_id", nullable = false)
    private String claimantPartyId;

    @Column(name = "defendant_party_id", nullable = false)
    private String defendantPartyId;

    @Column(name = "description", nullable = false)
    private String description;

    @Column(name = "status", nullable = false)
    private String status = "pending";

    /** AI creates claims as 'suggested'; humans move them to 'approved'. */
    @Column(name = "review_status", nullable = false)
    private String reviewStatus = "approved";

    @Column(name = "source_locator_id")
    private String sourceLocatorId;
}
