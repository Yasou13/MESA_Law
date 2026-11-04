package com.mesalaw.dto;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.mesalaw.entity.review.ReviewState;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

/** Request and response DTOs for review pipeline endpoints. */
public final class ReviewDto {

    private ReviewDto() {
    }

    @Data
    public static class ReviewItemResponse {
        private String id;
        private String matterId;
        private String entityType;
        private String entityId;
        private String proposedContent;
        private String correctedContent;
        private ReviewState status;
        private String suggestionId;
        private String decisionReason;
        private int versionId;
    }

    @Data
    public static class ApproveRequest {
        @NotNull @Min(1) private Integer expectedVersion;
        @Size(min = 3, max = 1000) private String reason;
    }

    @Data
    public static class RejectRequest {
        @NotNull @Min(1) private Integer expectedVersion;
        @NotNull @Size(min = 3, max = 1000) private String reason;
    }

    @Data
    public static class CorrectRequest {
        @NotNull @Min(1) private Integer expectedVersion;
        @NotNull @Size(min = 3, max = 1000) private String reason;
        @NotNull private String correctedContent;
    }

    @Data
    public static class MutationResponse {
        private String id;
        private ReviewState status;
        private int versionId;
        private String publicationJobId;

        public MutationResponse(String id, ReviewState status, int versionId) {
            this.id = id;
            this.status = status;
            this.versionId = versionId;
        }

        public MutationResponse(String id, ReviewState status, int versionId, String publicationJobId) {
            this(id, status, versionId);
            this.publicationJobId = publicationJobId;
        }
    }

    // ── Review context (GET /reviews/{reviewId}/context) ──

    @Data
    public static class SuggestionContext {
        private String id;
        private String suggestionType;
        private String extractorName;
        private String extractorVersion;
        private String parserVersion;
        private String confidenceCategory;
    }

    @Data
    public static class SourceContext {
        private String documentId;
        private String documentTitle;
        private String revisionId;
        private Integer pageNumber;
        private String chunkId;
        private Integer textStart;
        private Integer textEnd;
        private Map<String, Double> bbox;
        private String evidenceText;
        private String evidenceSha256;
        private String parserVersion;
        private String extractionVersion;
        private String provenanceState;
    }

    @Data
    public static class AuditEntry {
        private String id;
        private String action;
        private String userId;
        private OffsetDateTime createdAt;
        private String details;
    }

    @Data
    public static class ReviewContextResponse {
        private ReviewItemResponse review;
        private SuggestionContext suggestion;
        private SourceContext source;
        private List<AuditEntry> history = new ArrayList<>();
    }
}
