package com.mesalaw.dto;

import com.mesalaw.entity.matter.Claim;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO classes for domain data endpoints.
 * Replaces Python's ClaimResponse from routers/domain_data.py.
 */
public final class DomainDataDto {

    private DomainDataDto() {
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class ClaimResponse {
        private String id;
        private String matterId;
        private String claimantPartyId;
        private String defendantPartyId;
        private String description;
        private String status;
        private String reviewStatus;
        private String sourceLocatorId;

        public static ClaimResponse from(Claim c) {
            return ClaimResponse.builder()
                    .id(c.getId())
                    .matterId(c.getMatterId())
                    .claimantPartyId(c.getClaimantPartyId())
                    .defendantPartyId(c.getDefendantPartyId())
                    .description(c.getDescription())
                    .status(c.getStatus())
                    .reviewStatus(c.getReviewStatus())
                    .sourceLocatorId(c.getSourceLocatorId())
                    .build();
        }
    }
}
