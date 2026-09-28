package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.queue.Job;
import com.mesalaw.entity.mesa.MesaScopeBinding;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.JobRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * MESA Core v4 binding endpoints.
 * Replaces Python's routers/mesa_bindings.py.
 */
@RestController
@RequiredArgsConstructor
public class MesaBindingController {

    private final EntityManager entityManager;
    private final JobRepository jobRepository;

    @Data
    public static class MesaBindingCreate {
        @NotBlank @Size(max = 128) private String mesaTenantId;
        @NotBlank @Size(max = 128) private String workspaceId;
        @NotBlank @Size(max = 128) private String datasetId;
        @NotBlank @Size(max = 128) private String agentId;
    }

    @Data @AllArgsConstructor
    public static class MesaBindingResponse {
        private String id, matterId, mesaTenantId, workspaceId, datasetId, agentId;
        private String provisioningStatus;
        private OffsetDateTime lastVerifiedAt;
        private String lastError;
    }

    /**
     * GET /matters/{matterId}/mesa-binding — Get MESA binding.
     * Matches Python: GET /matters/{matter_id}/mesa-binding
     */
    @GetMapping("/matters/{matterId}/mesa-binding")
    public MesaBindingResponse getMesaBinding(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        MesaScopeBinding binding = entityManager.createQuery(
                "SELECT b FROM MesaScopeBinding b WHERE b.tenantId = :tid AND b.matterId = :mid",
                MesaScopeBinding.class)
                .setParameter("tid", ctx.tenantId()).setParameter("mid", matterId)
                .getResultStream().findFirst()
                .orElseThrow(() -> new ProblemException(404, "Not Found", "MESA binding not found"));

        return toResponse(binding);
    }

    /**
     * PUT /matters/{matterId}/mesa-binding — Create MESA binding (immutable).
     * Matches Python: PUT /matters/{matter_id}/mesa-binding
     */
    @PutMapping("/matters/{matterId}/mesa-binding")
    @ResponseStatus(HttpStatus.CREATED)
    public MesaBindingResponse createMesaBinding(
            @PathVariable String matterId,
            @Valid @RequestBody MesaBindingCreate request) {

        RequestContext ctx = RequestContextHolder.get();

        // Check existing
        long existing = entityManager.createQuery(
                "SELECT COUNT(b) FROM MesaScopeBinding b WHERE b.tenantId = :tid AND b.matterId = :mid", Long.class)
                .setParameter("tid", ctx.tenantId()).setParameter("mid", matterId)
                .getSingleResult();
        if (existing > 0) {
            throw new ProblemException(409, "Conflict", "MESA binding already exists and is immutable");
        }

        MesaScopeBinding binding = new MesaScopeBinding();
        binding.setTenantId(ctx.tenantId());
        binding.setMatterId(matterId);
        binding.setMesaTenantId(request.getMesaTenantId());
        binding.setWorkspaceId(request.getWorkspaceId());
        binding.setDatasetId(request.getDatasetId());
        binding.setAgentId(request.getAgentId());
        binding.setProvisioningStatus("PENDING_PREFLIGHT");
        entityManager.persist(binding);

        // Enqueue provisioning job
        Job job = new Job();
        job.setType("PROVISION_MESA_SCOPE");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(matterId);
        job.setRequestedBy(ctx.principalId());
        job.setIdempotencyKey("mesa-preflight:" + binding.getId());
        job.setPayload("{\"binding_id\":\"" + binding.getId() + "\",\"matter_id\":\"" + matterId + "\"}");
        entityManager.persist(job);

        entityManager.flush();
        return toResponse(binding);
    }

    private MesaBindingResponse toResponse(MesaScopeBinding b) {
        return new MesaBindingResponse(
                b.getId(), b.getMatterId(), b.getMesaTenantId(),
                b.getWorkspaceId(), b.getDatasetId(), b.getAgentId(),
                b.getProvisioningStatus(), b.getLastVerifiedAt(), b.getLastError());
    }
}
