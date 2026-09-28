package com.mesalaw.entity.review;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A structured legal assertion (subject-predicate-object triple) with provenance.
 * Replaces Python's {@code LegalAssertion} from models/domain.py.
 */
@Entity
@Table(name = "legal_assertions")
@Getter
@Setter
@NoArgsConstructor
public class LegalAssertion extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "claim_id")
    private String claimId;

    @Column(name = "evidence_id")
    private String evidenceId;

    @Column(name = "legal_source_id")
    private String legalSourceId;

    @Column(name = "assertion_text", nullable = false)
    private String assertionText;

    @Column(name = "source_locator_id")
    private String sourceLocatorId;

    @Column(name = "review_id")
    private String reviewId;

    @Column(name = "review_version")
    private Integer reviewVersion;

    @Column(name = "review_status", nullable = false)
    private String reviewStatus = "approved";

    @Column(name = "assertion_type")
    private String assertionType;

    @Column(name = "subject_text", columnDefinition = "TEXT")
    private String subjectText;

    @Column(name = "predicate")
    private String predicate;

    @Column(name = "object_text", columnDefinition = "TEXT")
    private String objectText;

    @Column(name = "object_data", columnDefinition = "jsonb")
    private String objectData;

    @Column(name = "polarity")
    private String polarity;

    @Column(name = "modality")
    private String modality;

    @Column(name = "canonical_status", nullable = false)
    private String canonicalStatus = "LEGACY_UNTYPED";

    @Column(name = "publication_status", nullable = false)
    private String publicationStatus = "NOT_PUBLISHED";
}
