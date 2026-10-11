package com.mesalaw.dto;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

/** Response DTOs for parsed-document and parsed-page endpoints. */
public final class ParsedDocumentDto {

    private ParsedDocumentDto() {
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ParsedDocumentResponse(
            String id,
            String documentId,
            String revisionId,
            int parsingRevision,
            String parserUsed,
            String status) {
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record ParsedPageResponse(
            String id,
            int pageNumber,
            String textContent,
            JsonNode layoutData) {
    }
}
