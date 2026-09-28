package com.mesalaw.dto;

import java.util.List;
import java.util.Set;

import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * DTO classes for Session endpoints.
 * Replaces Python's SessionContextResponse, ActiveFirmResponse from routers/session.py.
 */
public final class SessionDto {

    private SessionDto() {}

    @Data
    @AllArgsConstructor
    public static class ContextResponse {
        private String status;
        private String tenantId;
        private String principalId;
        private Set<String> roles;
    }

    @Data
    @AllArgsConstructor
    public static class ActiveFirmResponse {
        private String status;
        private String activeFirmId;
        private String role;
    }

    @Data
    public static class SetActiveFirmRequest {
        private String firmId;
    }
}
