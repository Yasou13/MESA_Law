package com.mesalaw.dto;

import java.time.OffsetDateTime;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import lombok.Builder;

public final class DocumentDto {

    private DocumentDto() {}

    @Data
    public static class UploadIntentRequest {
        @NotBlank private String matterId;
        @NotBlank @Size(max = 255) private String filename;
        @NotBlank @Size(max = 100) private String mimeType;
        @Min(1) @Max(104857600) private long sizeBytes;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class UploadIntentResponse {
        private String documentId;
        private String revisionId;
        private String presignedUrl;
        private String storageKey;
    }

    @Data
    public static class DocumentResponse {
        private String id;
        private String matterId;
        private String title;
        private String status;
        private String latestRevisionId;
        private String provenanceState;
        private String failureReason;
        private OffsetDateTime createdAt;
    }
}
