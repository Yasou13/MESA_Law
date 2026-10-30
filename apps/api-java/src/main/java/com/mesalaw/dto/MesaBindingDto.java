package com.mesalaw.dto;

import java.time.OffsetDateTime;

import com.mesalaw.entity.mesa.MesaScopeBinding;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO classes for MESA binding endpoints.
 * Replaces Python's MesaBindingCreate / MesaBindingResponse from routers/mesa_bindings.py.
 */
public final class MesaBindingDto {

    private MesaBindingDto() {
    }

    @Data
    public static class CreateRequest {
        @NotBlank @Size(min = 1, max = 128) private String mesaTenantId;
        @NotBlank @Size(min = 1, max = 128) private String workspaceId;
        @NotBlank @Size(min = 1, max = 128) private String datasetId;
        @NotBlank @Size(min = 1, max = 128) private String agentId;
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Response {
        private String id;
        private String matterId;
        private String mesaTenantId;
        private String workspaceId;
        private String datasetId;
        private String agentId;
        private String provisioningStatus;
        private OffsetDateTime lastVerifiedAt;
        private String lastError;
        private Integer versionId;

        public static Response from(MesaScopeBinding b) {
            return Response.builder()
                    .id(b.getId())
                    .matterId(b.getMatterId())
                    .mesaTenantId(b.getMesaTenantId())
                    .workspaceId(b.getWorkspaceId())
                    .datasetId(b.getDatasetId())
                    .agentId(b.getAgentId())
                    .provisioningStatus(b.getProvisioningStatus())
                    .lastVerifiedAt(b.getLastVerifiedAt())
                    .lastError(b.getLastError())
                    .versionId(b.getVersionId())
                    .build();
        }
    }
}
