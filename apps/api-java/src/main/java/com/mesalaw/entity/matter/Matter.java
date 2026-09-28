package com.mesalaw.entity.matter;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Legal matter (case/dossier) within a firm.
 * Replaces Python's {@code Matter} from models/domain.py.
 *
 * <p>Central entity — documents, claims, deadlines, reviews all belong to a matter.</p>
 */
@Entity
@Table(name = "matters")
@Getter
@Setter
@NoArgsConstructor
public class Matter extends TenantAwareEntity {

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "internal_reference")
    private String internalReference;

    @Column(name = "status", nullable = false)
    private String status = "open";

    @Column(name = "client_name")
    private String clientName;

    @Column(name = "responsible_attorney_id")
    private String responsibleAttorneyId;

    @Column(name = "jurisdiction")
    private String jurisdiction;

    @Column(name = "case_type")
    private String caseType;

    @Column(name = "confidentiality_level", nullable = false)
    private String confidentialityLevel = "standard";

    @Column(name = "ai_processing_policy", nullable = false)
    private String aiProcessingPolicy = "standard";

    @Column(name = "opened_at")
    private OffsetDateTime openedAt;

    @Column(name = "closed_at")
    private OffsetDateTime closedAt;
}
