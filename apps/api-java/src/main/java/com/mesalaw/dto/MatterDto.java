package com.mesalaw.dto;

import java.time.OffsetDateTime;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO classes for Matter endpoints.
 * Replaces Python's MatterCreate, MatterResponse from schemas/api.py.
 */
public final class MatterDto {

    private MatterDto() {}

    @Data
    public static class CreateRequest {
        @NotBlank
        @Size(min = 3, max = 255)
        private String title;

        private String internalReference;
        private String clientName;
        private String jurisdiction;
        private String caseType;
        private String confidentialityLevel = "standard";
        private String aiProcessingPolicy = "standard";
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Response {
        private String id;
        private String title;
        private String internalReference;
        private String status;
        private String clientName;
        private String jurisdiction;
        private String caseType;
        private String confidentialityLevel;
        private String aiProcessingPolicy;
        private String openedAt;
        private String closedAt;
        private String accessScope;
        private String responsibleAttorney;
        private OffsetDateTime createdAt;
        private OffsetDateTime updatedAt;
    }
}
