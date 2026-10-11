package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
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
import com.mesalaw.entity.matter.Claim;
import com.mesalaw.entity.matter.ClaimEvidenceLink;
import com.mesalaw.entity.matter.EvidenceItem;
import com.mesalaw.entity.matter.MatterEvent;
import com.mesalaw.entity.matter.MatterParty;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.ClaimEvidenceLinkRepository;
import com.mesalaw.repository.ClaimRepository;
import com.mesalaw.repository.EvidenceItemRepository;
import com.mesalaw.repository.MatterEventRepository;
import com.mesalaw.repository.MatterMemberRepository;
import com.mesalaw.repository.MatterPartyRepository;
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
        private final MatterPartyRepository matterPartyRepository;
        private final EvidenceItemRepository evidenceItemRepository;
        private final ClaimRepository claimRepository;
        private final ClaimEvidenceLinkRepository claimEvidenceLinkRepository;
        private final MatterEventRepository matterEventRepository;

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

        /**
         * GET /matters/{matterId}/parties — List parties involved in a matter.
         */
        @GetMapping("/{matterId}/parties")
        public List<MatterDto.PartyResponse> getMatterParties(@PathVariable String matterId) {
                RequestContext ctx = RequestContextHolder.get();
                matterRepository.findByIdAndTenantId(matterId, ctx.tenantId())
                                .orElseThrow(() -> new ProblemException(404, "Not Found", "Matter not found"));

                return matterPartyRepository.findByMatterIdAndTenantIdAndDeletedFalse(matterId, ctx.tenantId())
                                .stream()
                                .map(p -> MatterDto.PartyResponse.builder()
                                                .id(p.getId())
                                                .name(p.getName())
                                                .role(p.getRole())
                                                .type(p.getType())
                                                .build())
                                .collect(Collectors.toList());
        }

        /**
         * GET /matters/{matterId}/evidence — List evidence items for a matter.
         */
        @GetMapping("/{matterId}/evidence")
        public List<MatterDto.EvidenceResponse> getMatterEvidence(@PathVariable String matterId) {
                RequestContext ctx = RequestContextHolder.get();
                matterRepository.findByIdAndTenantId(matterId, ctx.tenantId())
                                .orElseThrow(() -> new ProblemException(404, "Not Found", "Matter not found"));

                return evidenceItemRepository.findByMatterIdAndTenantIdAndDeletedFalse(matterId, ctx.tenantId())
                                .stream()
                                .map(e -> MatterDto.EvidenceResponse.builder()
                                                .id(e.getId())
                                                .description(e.getDescription())
                                                .documentId(e.getDocumentId())
                                                .reviewStatus(e.getReviewStatus())
                                                .build())
                                .collect(Collectors.toList());
        }

        /**
         * GET /matters/{matterId}/claims-evidence — List claims and their evidence
         * links.
         */
        @GetMapping("/{matterId}/claims-evidence")
        public MatterDto.ClaimEvidenceResponse getClaimsAndEvidence(@PathVariable String matterId) {
                RequestContext ctx = RequestContextHolder.get();
                matterRepository.findByIdAndTenantId(matterId, ctx.tenantId())
                                .orElseThrow(() -> new ProblemException(404, "Not Found", "Matter not found"));

                List<Claim> claims = claimRepository.findByMatterIdAndTenantIdAndDeletedFalse(matterId, ctx.tenantId());

                List<String> claimIds = claims.stream().map(Claim::getId).collect(Collectors.toList());
                List<ClaimEvidenceLink> links = new ArrayList<>();
                if (!claimIds.isEmpty()) {
                        links = claimEvidenceLinkRepository.findByClaimIdInAndTenantIdAndDeletedFalse(claimIds,
                                        ctx.tenantId());
                }

                List<MatterDto.ClaimResponse> claimDtos = claims.stream()
                                .map(c -> MatterDto.ClaimResponse.builder()
                                                .id(c.getId())
                                                .description(c.getDescription())
                                                .claimantPartyId(c.getClaimantPartyId())
                                                .defendantPartyId(c.getDefendantPartyId())
                                                .status(c.getStatus())
                                                .reviewStatus(c.getReviewStatus())
                                                .build())
                                .collect(Collectors.toList());

                List<MatterDto.ClaimEvidenceResponse.LinkResponse> linkDtos = links.stream()
                                .map(l -> MatterDto.ClaimEvidenceResponse.LinkResponse.builder()
                                                .claimId(l.getClaimId())
                                                .evidenceId(l.getEvidenceId())
                                                .supportType(l.getSupportType())
                                                .build())
                                .collect(Collectors.toList());

                return MatterDto.ClaimEvidenceResponse.builder()
                                .claims(claimDtos)
                                .links(linkDtos)
                                .build();
        }

        /**
         * GET /matters/{matterId}/timeline — List the chronological timeline of events
         * for a matter.
         */
        @GetMapping("/{matterId}/timeline")
        public List<MatterDto.TimelineEventResponse> getMatterTimeline(@PathVariable String matterId) {
                RequestContext ctx = RequestContextHolder.get();
                matterRepository.findByIdAndTenantId(matterId, ctx.tenantId())
                                .orElseThrow(() -> new ProblemException(404, "Not Found", "Matter not found"));

                return matterEventRepository
                                .findByMatterIdAndTenantIdAndDeletedFalseOrderByEventDateAsc(matterId, ctx.tenantId())
                                .stream()
                                .map(e -> MatterDto.TimelineEventResponse.builder()
                                                .id(e.getId())
                                                .eventType(e.getEventType())
                                                .description(e.getDescription())
                                                .eventDate(e.getEventDate() != null ? e.getEventDate().toString()
                                                                : null)
                                                .datePrecision(e.getDatePrecision())
                                                .reviewState(e.getReviewState())
                                                .sourceType(e.getSourceType())
                                                .confidence(e.getConfidence())
                                                .build())
                                .collect(Collectors.toList());
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
