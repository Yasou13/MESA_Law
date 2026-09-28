package com.mesalaw.dto;

import java.time.OffsetDateTime;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * DTO classes for Firm endpoints.
 * Replaces Python's FirmCreateRequest, FirmResponse, FirmMemberResponse from routers/firms.py.
 */
public final class FirmDto {

    private FirmDto() {}

    @Data
    public static class CreateRequest {
        @NotBlank
        @Size(min = 2, max = 100)
        private String name;
    }

    @Data
    public static class Response {
        private String id;
        private String name;

        public Response(String id, String name) {
            this.id = id;
            this.name = name;
        }
    }

    @Data
    public static class MemberResponse {
        private String id;
        private String email;
        private String fullName;
        private String role;
        private boolean active;

        public MemberResponse(String id, String email, String fullName, String role, boolean active) {
            this.id = id;
            this.email = email;
            this.fullName = fullName;
            this.role = role;
            this.active = active;
        }
    }

    @Data
    public static class RoleElevationRequest {
        @NotBlank
        private String role;
    }
}
