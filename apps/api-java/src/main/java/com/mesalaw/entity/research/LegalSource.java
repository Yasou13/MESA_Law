package com.mesalaw.entity.research;

import com.mesalaw.entity.base.BaseEntity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A legal source (case law, statute, regulation) from a source package.
 * Replaces Python's {@code LegalSource} from models/research.py.
 */
@Entity
@Table(name = "legal_sources")
@Getter
@Setter
@NoArgsConstructor
public class LegalSource extends BaseEntity {

    @Column(name = "source_package_id", nullable = false)
    private String sourcePackageId;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "citation", nullable = false)
    private String citation;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "source_type", nullable = false)
    private String sourceType;

    @Column(name = "jurisdiction")
    private String jurisdiction;

    @Column(name = "court")
    private String court;

    @Column(name = "chamber")
    private String chamber;

    @Column(name = "decision_number")
    private String decisionNumber;

    @Column(name = "decision_date")
    private OffsetDateTime decisionDate;

    @Column(name = "effective_from")
    private OffsetDateTime effectiveFrom;

    @Column(name = "effective_to")
    private OffsetDateTime effectiveTo;

    @Column(name = "status", nullable = false)
    private String status = "CURRENT";

    @Column(name = "license_type")
    private String licenseType;

    @Column(name = "snapshot_id")
    private String snapshotId;

    @Column(name = "content_hash")
    private String contentHash;
}
