package com.mesalaw.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** Request and response DTOs for Draft Studio endpoints. */
public final class DraftDto {

    private DraftDto() {
    }

    @Data
    public static class CreateDraftRequest {
        @NotBlank
        private String matterId;

        @NotBlank
        private String title;

        private String content = "";
    }

    @Data
    public static class UpdateDraftRequest {
        @NotBlank
        private String content;

        @NotNull
        @Min(1)
        @JsonProperty("expected_version")
        private Integer expectedVersion;

        private String changeSummary;
    }

    @Data
    public static class DraftResponse {
        private String id;
        private String matterId;
        private String title;
        private String content;
        private int version;
        private String status;
    }

    // ── New DTOs for remaining endpoints ──

    @Data
    public static class DraftCitationResponse {
        private String id;
        private String documentId;
        private String citationText;
        private String verificationState;
    }

    @Data
    public static class DraftStatusResponse {
        private String status;
    }

    @Data
    public static class ExportDraftRequest {
        @NotBlank
        private String format; // "pdf" or "docx"
    }

    @Data
    public static class ExportDraftResponse {
        private String message;
        private String jobId;
        private String format;
        private int version;
    }

    @Data
    public static class GenerateDraftRequest {
        @NotBlank
        private String matterId;

        private String templateName;
    }

    @Data
    public static class GenerateDraftResponse {
        private String message;
        private String jobId;
    }
}
