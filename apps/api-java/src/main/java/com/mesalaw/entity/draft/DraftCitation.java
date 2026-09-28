package com.mesalaw.entity.draft;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A verified citation linking a draft paragraph to a source document.
 * Replaces Python's {@code DraftCitation} from models/draft.py.
 */
@Entity
@Table(name = "draft_citations")
@Getter
@Setter
@NoArgsConstructor
public class DraftCitation extends TenantAwareEntity {

    @Column(name = "draft_id", nullable = false)
    private String draftId;

    @Column(name = "draft_revision_id")
    private String draftRevisionId;

    @Column(name = "document_id")
    private String documentId;

    @Column(name = "document_revision_id")
    private String documentRevisionId;

    @Column(name = "source_locator_id")
    private String sourceLocatorId;

    @Column(name = "citation_text", nullable = false)
    private String citationText;

    @Column(name = "verification_state", nullable = false)
    private String verificationState = "unverified";
}
