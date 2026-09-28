package com.mesalaw.entity.review;

import com.mesalaw.entity.base.BaseEntity;

import java.time.OffsetDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A review item linking an AI-proposed entity to a human review decision.
 * Replaces Python's {@code ReviewItem} from models/review.py.
 */
@Entity
@Table(name = "review_items")
@Getter
@Setter
@NoArgsConstructor
public class ReviewItem extends BaseEntity {

    @Column(name = "tenant_id", nullable = false)
    private String tenantId;

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "entity_type", nullable = false)
    private String entityType;

    @Column(name = "entity_id", nullable = false)
    private String entityId;

    @Column(name = "suggestion_id")
    private String suggestionId;

    @Column(name = "proposed_content", nullable = false, columnDefinition = "jsonb")
    private String proposedContent;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 32)
    private ReviewState status = ReviewState.PROPOSED;

    @Column(name = "external_use_ready_at")
    private OffsetDateTime externalUseReadyAt;

    @Column(name = "reviewed_by")
    private String reviewedBy;

    @Column(name = "reviewed_at")
    private OffsetDateTime reviewedAt;

    @Column(name = "corrected_content", columnDefinition = "jsonb")
    private String correctedContent;

    @Column(name = "decision_reason")
    private String decisionReason;
}
