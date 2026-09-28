package com.mesalaw.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.draft.Draft;
import com.mesalaw.entity.draft.DraftRevision;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.DraftRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Draft studio endpoints — CRUD + versioned save.
 * Replaces Python's routers/draft_studio.py.
 */
@RestController
@RequestMapping("/drafts")
@RequiredArgsConstructor
public class DraftController {

    private final DraftRepository draftRepository;
    // DraftRevisionRepository not yet created — will use EntityManager for now
    private final jakarta.persistence.EntityManager entityManager;

    // ── DTOs ──

    @Data
    public static class CreateDraftRequest {
        @NotBlank private String matterId;
        @NotBlank private String title;
        private String content = "";
    }

    @Data
    public static class UpdateDraftRequest {
        @NotBlank private String content;
        @NotBlank private String etag;
        private String changeSummary;
    }

    @Data
    public static class DraftResponse {
        private String id;
        private String matterId;
        private String title;
        private String content;
        private int version;
        private String etag;
        private String status;
    }

    // ── Endpoints ──

    /**
     * GET /drafts/matters/{matterId} — List drafts for a matter.
     */
    @GetMapping("/matters/{matterId}")
    public List<DraftResponse> listDrafts(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<Draft> drafts = draftRepository
                .findByTenantIdAndMatterIdAndDeletedFalse(ctx.tenantId(), matterId);

        return drafts.stream().map(this::toResponse).collect(Collectors.toList());
    }

    /**
     * GET /drafts/{draftId} — Get a single draft.
     */
    @GetMapping("/{draftId}")
    public DraftResponse getDraft(@PathVariable String draftId) {
        Draft draft = getAndValidateDraft(draftId);
        return toResponse(draft);
    }

    /**
     * POST /drafts — Create a new draft.
     */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public DraftResponse createDraft(@Valid @RequestBody CreateDraftRequest request) {
        RequestContext ctx = RequestContextHolder.get();

        Draft draft = new Draft();
        draft.setTenantId(ctx.tenantId());
        draft.setMatterId(request.getMatterId());
        draft.setTitle(request.getTitle());
        draft.setContent(request.getContent());
        draft.setVersion(1);
        draft.setEtag("v1");
        draft.setStatus("draft");
        draftRepository.save(draft);

        return toResponse(draft);
    }

    /**
     * PUT /drafts/{draftId} — Update draft content with ETag-based concurrency.
     */
    @PutMapping("/{draftId}")
    public DraftResponse updateDraft(
            @PathVariable String draftId,
            @Valid @RequestBody UpdateDraftRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        Draft draft = getAndValidateDraft(draftId);

        // ETag concurrency check
        if (!draft.getEtag().equals(request.getEtag())) {
            throw new ProblemException(409, "Conflict",
                    "Draft has been modified. Expected ETag: " + request.getEtag()
                            + ", current: " + draft.getEtag());
        }

        // Create revision snapshot
        DraftRevision revision = new DraftRevision();
        revision.setTenantId(ctx.tenantId());
        revision.setDraftId(draft.getId());
        revision.setVersion(draft.getVersion());
        revision.setContent(draft.getContent());
        revision.setChangeSummary(request.getChangeSummary());
        entityManager.persist(revision);

        // Update draft
        draft.setContent(request.getContent());
        draft.setVersion(draft.getVersion() + 1);
        draft.setEtag("v" + draft.getVersion());
        draftRepository.save(draft);

        return toResponse(draft);
    }

    // ── Helpers ──

    private Draft getAndValidateDraft(String draftId) {
        RequestContext ctx = RequestContextHolder.get();
        Draft draft = draftRepository.findById(draftId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Draft not found"));

        if (!draft.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Draft not found");
        }
        return draft;
    }

    private DraftResponse toResponse(Draft d) {
        DraftResponse resp = new DraftResponse();
        resp.setId(d.getId());
        resp.setMatterId(d.getMatterId());
        resp.setTitle(d.getTitle());
        resp.setContent(d.getContent());
        resp.setVersion(d.getVersion());
        resp.setEtag(d.getEtag());
        resp.setStatus(d.getStatus());
        return resp;
    }
}
