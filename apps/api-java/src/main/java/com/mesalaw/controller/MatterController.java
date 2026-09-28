package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.MatterDto;
import com.mesalaw.entity.matter.Matter;
import com.mesalaw.entity.matter.MatterMember;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.MatterMemberRepository;
import com.mesalaw.repository.MatterRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * Matter (case/dossier) CRUD endpoints.
 * Replaces Python's routers/matters.py.
 */
@RestController
@RequestMapping("/matters")
@RequiredArgsConstructor
public class MatterController {

    private final MatterRepository matterRepository;
    private final MatterMemberRepository matterMemberRepository;

    /**
     * GET /matters — List all matters for the current tenant.
     * Matches Python: GET /matters → listMatters
     */
    @GetMapping
    public List<MatterDto.Response> listMatters() {
        RequestContext ctx = RequestContextHolder.get();
        List<Matter> matters = matterRepository.findByTenantIdAndDeletedFalse(ctx.tenantId());

        return matters.stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    /**
     * GET /matters/{matterId} — Get a specific matter.
     * Matches Python: GET /matters/{matter_id} → getMatter
     */
    @GetMapping("/{matterId}")
    public MatterDto.Response getMatter(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        Matter matter = matterRepository.findByIdAndTenantId(matterId, ctx.tenantId())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Matter not found"));

        return toResponse(matter);
    }

    /**
     * POST /matters — Create a new matter.
     * Matches Python: POST /matters → createMatter
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public MatterDto.Response createMatter(@Valid @RequestBody MatterDto.CreateRequest request) {
        RequestContext ctx = RequestContextHolder.get();

        Matter matter = new Matter();
        matter.setTenantId(ctx.tenantId());
        matter.setTitle(request.getTitle());
        matter.setInternalReference(request.getInternalReference());
        matter.setClientName(request.getClientName());
        matter.setJurisdiction(request.getJurisdiction());
        matter.setCaseType(request.getCaseType());
        matter.setConfidentialityLevel(request.getConfidentialityLevel());
        matter.setAiProcessingPolicy(request.getAiProcessingPolicy());
        matter.setStatus("open");
        matter.setOpenedAt(OffsetDateTime.now());
        matter.setResponsibleAttorneyId(ctx.principalId());

        matterRepository.save(matter);

        // Auto-add creator as admin member
        MatterMember member = new MatterMember();
        member.setTenantId(ctx.tenantId());
        member.setMatterId(matter.getId());
        member.setUserId(ctx.principalId());
        member.setAccessScope("admin");
        matterMemberRepository.save(member);

        return toResponse(matter);
    }

    private MatterDto.Response toResponse(Matter m) {
        return MatterDto.Response.builder()
                .id(m.getId())
                .title(m.getTitle())
                .internalReference(m.getInternalReference())
                .status(m.getStatus())
                .clientName(m.getClientName())
                .jurisdiction(m.getJurisdiction())
                .caseType(m.getCaseType())
                .confidentialityLevel(m.getConfidentialityLevel())
                .aiProcessingPolicy(m.getAiProcessingPolicy())
                .openedAt(m.getOpenedAt() != null ? m.getOpenedAt().toString() : null)
                .closedAt(m.getClosedAt() != null ? m.getClosedAt().toString() : null)
                .responsibleAttorney(m.getResponsibleAttorneyId())
                .createdAt(m.getCreatedAt())
                .updatedAt(m.getUpdatedAt())
                .build();
    }
}
