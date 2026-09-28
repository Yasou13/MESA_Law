package com.mesalaw.entity.review;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Raw AI extraction suggestion before human review.
 * Replaces Python's {@code ExtractionSuggestion} from models/review.py.
 */
@Entity
@Table(name = "extraction_suggestions")
@Getter
@Setter
@NoArgsConstructor
public class ExtractionSuggestion extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "document_id", nullable = false)
    private String documentId;

    @Column(name = "document_revision_id", nullable = false)
    private String documentRevisionId;

    @Column(name = "source_locator_id")
    private String sourceLocatorId;

    @Column(name = "suggestion_type", nullable = false)
    private String suggestionType;

    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private String payload;

    @Column(name = "extractor_name", nullable = false)
    private String extractorName;

    @Column(name = "extractor_version", nullable = false)
    private String extractorVersion;

    @Column(name = "prompt_version", nullable = false)
    private String promptVersion;

    @Column(name = "parser_version", nullable = false)
    private String parserVersion;

    @Column(name = "confidence_category")
    private String confidenceCategory = "high";

    @Column(name = "review_state")
    private String reviewState = "pending";

    @Column(name = "idempotency_key", nullable = false, unique = true)
    private String idempotencyKey;
}
