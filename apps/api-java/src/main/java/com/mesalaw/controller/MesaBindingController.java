package com.mesalaw.controller;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mesalaw.dto.MesaBindingDto;
import com.mesalaw.entity.mesa.MesaScopeBinding;
import com.mesalaw.entity.queue.Job;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.JobRepository;
import com.mesalaw.repository.MesaScopeBindingRepository;
import com.mesalaw.security.MatterAccessGuard;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * MESA Core v4 binding endpoints.
 * Replaces Python's routers/mesa_bindings.py.
 */
@RestController
@RequiredArgsConstructor
public class MesaBindingController {

    private final MesaScopeBindingRepository bindingRepository;
    private final JobRepository jobRepository;
    private final MatterAccessGuard accessGuard;
    private final ObjectMapper objectMapper;

    /**
     * GET /matters/{matterId}/mesa-binding — Get MESA binding.
     * Matches Python: GET /matters/{matter_id}/mesa-binding
     */
    @GetMapping("/matters/{matterId}/mesa-binding")
    @Transactional(readOnly = true)
    public MesaBindingDto.Response getMesaBinding(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        accessGuard.canRead(ctx, matterId);

        MesaScopeBinding binding = bindingRepository.findByTenantIdAndMatterId(ctx.tenantId(), matterId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "MESA binding not found"));
        return MesaBindingDto.Response.from(binding);
    }

    /**
     * PUT /matters/{matterId}/mesa-binding — Create MESA binding (immutable).
     * Matches Python: PUT /matters/{matter_id}/mesa-binding
     */
    @PutMapping("/matters/{matterId}/mesa-binding")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public MesaBindingDto.Response createMesaBinding(
            @PathVariable String matterId,
            @Valid @RequestBody MesaBindingDto.CreateRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        accessGuard.canWrite(ctx, matterId);

        if (bindingRepository.existsByTenantIdAndMatterId(ctx.tenantId(), matterId)) {
            throw new ProblemException(409, "Conflict",
                    "MESA binding already exists and is immutable; inspect its status");
        }
        // DB has a unique (tenant_id, dataset_id) constraint — fail with 409 instead of a 500.
        if (bindingRepository.existsByTenantIdAndDatasetId(ctx.tenantId(), request.getDatasetId())) {
            throw new ProblemException(409, "Conflict", "Dataset is already bound to another matter");
        }

        MesaScopeBinding binding = new MesaScopeBinding();
        binding.setTenantId(ctx.tenantId());
        binding.setMatterId(matterId);
        binding.setMesaTenantId(request.getMesaTenantId());
        binding.setWorkspaceId(request.getWorkspaceId());
        binding.setDatasetId(request.getDatasetId());
        binding.setAgentId(request.getAgentId());
        binding.setProvisioningStatus("PENDING_PREFLIGHT");
        binding.setCreatedBy(ctx.principalId());

        try {
            binding = bindingRepository.saveAndFlush(binding);
        } catch (DataIntegrityViolationException e) {
            // Concurrent create raced past the existence checks.
            throw new ProblemException(409, "Conflict",
                    "MESA binding already exists and is immutable; inspect its status", e);
        }

        // Enqueue provisioning (preflight) job for the Python worker
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("binding_id", binding.getId());
        payload.put("matter_id", matterId);

        Job job = new Job();
        job.setType("PROVISION_MESA_SCOPE");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(matterId);
        job.setRequestedBy(ctx.principalId());
        job.setIdempotencyKey("mesa-preflight:" + binding.getId() + ":" + binding.getVersionId());
        job.setPayload(toJson(payload));
        jobRepository.save(job);

        return MesaBindingDto.Response.from(binding);
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize JSON", e);
        }
    }
}
