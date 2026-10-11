package com.mesalaw.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.DraftDto.CreateDraftRequest;
import com.mesalaw.dto.DraftDto.DraftCitationResponse;
import com.mesalaw.dto.DraftDto.DraftResponse;
import com.mesalaw.dto.DraftDto.DraftStatusResponse;
import com.mesalaw.dto.DraftDto.ExportDraftRequest;
import com.mesalaw.dto.DraftDto.ExportDraftResponse;
import com.mesalaw.dto.DraftDto.GenerateDraftRequest;
import com.mesalaw.dto.DraftDto.GenerateDraftResponse;
import com.mesalaw.dto.DraftDto.UpdateDraftRequest;
import com.mesalaw.entity.draft.Draft;
import com.mesalaw.entity.draft.DraftCitation;
import com.mesalaw.entity.draft.DraftRevision;
import com.mesalaw.entity.queue.Job;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.DraftCitationRepository;
import com.mesalaw.repository.DraftRepository;
import com.mesalaw.repository.DraftRevisionRepository;
import com.mesalaw.repository.JobRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * Draft studio endpoints — CRUD + versioned save + workflow + job dispatch.
 * Replaces Python's routers/draft_studio.py.
 */
@RestController
@RequestMapping("/drafts")
@RequiredArgsConstructor
public class DraftController {

    private final DraftRepository draftRepository;
    private final DraftRevisionRepository draftRevisionRepository;
    private final DraftCitationRepository draftCitationRepository;
    private final JobRepository jobRepository;

    // ── List Endpoints ──

    /**
     * GET /drafts — List all drafts visible to the current user.
     * Filters through MatterMember to show only drafts for assigned matters.
     */
    @GetMapping
    public List<DraftResponse> listAllDrafts() {
        RequestContext ctx = RequestContextHolder.get();
        List<Draft> drafts = draftRepository.findAllByTenantAndUser(
                ctx.tenantId(), ctx.principalId());

        return drafts.stream().map(this::toResponse).collect(Collectors.toList());
    }

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

    // ── Single Draft ──

    /**
     * GET /drafts/{draftId} — Get a single draft.
     */
    @GetMapping("/{draftId}")
    public DraftResponse getDraft(@PathVariable String draftId) {
        Draft draft = getAndValidateDraft(draftId);
        return toResponse(draft);
    }

    // ── Create / Update ──

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
        draft.setStatus("draft");
        draftRepository.save(draft);

        return toResponse(draft);
    }

    /**
     * PUT /drafts/{draftId} — Update draft content with expected-version
     * concurrency.
     */
    @PutMapping("/{draftId}")
    @Transactional
    public DraftResponse updateDraft(
            @PathVariable String draftId,
            @Valid @RequestBody UpdateDraftRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        Draft draft = getAndValidateDraft(draftId);

        // Check the public draft revision; BaseEntity's @Version guards concurrent
        // writes.
        if (draft.getVersion() != request.getExpectedVersion()) {
            throw new ProblemException(409, "Conflict",
                    "Draft has been modified. Expected version: " + request.getExpectedVersion()
                            + ", current: " + draft.getVersion());
        }

        // Create revision snapshot
        DraftRevision revision = new DraftRevision();
        revision.setTenantId(ctx.tenantId());
        revision.setDraftId(draft.getId());
        revision.setVersion(draft.getVersion());
        revision.setContent(draft.getContent());
        revision.setChangeSummary(request.getChangeSummary());
        draftRevisionRepository.save(revision);

        // Update draft
        draft.setContent(request.getContent());
        draft.setVersion(draft.getVersion() + 1);

        // If the draft was approved and is now being edited again, revert to DRAFT
        // status
        if ("APPROVED_FOR_EXTERNAL_USE".equalsIgnoreCase(draft.getStatus())) {
            draft.setStatus("DRAFT");
        }

        draftRepository.save(draft);

        return toResponse(draft);
    }

    // ── Citations ──

    /**
     * GET /drafts/{draftId}/citations — Get LLM-generated citations for a draft.
     * Returns the source references the AI used when generating this draft.
     */
    @GetMapping("/{draftId}/citations")
    public List<DraftCitationResponse> getDraftCitations(@PathVariable String draftId) {
        getAndValidateDraft(draftId); // ensure draft exists & belongs to tenant

        List<DraftCitation> citations = draftCitationRepository.findByDraftId(draftId);

        return citations.stream().map(c -> {
            DraftCitationResponse resp = new DraftCitationResponse();
            resp.setId(c.getId());
            resp.setDocumentId(c.getDocumentId());
            resp.setCitationText(c.getCitationText());
            resp.setVerificationState(c.getVerificationState());
            return resp;
        }).collect(Collectors.toList());
    }

    // ── Workflow: Review & Approve ──

    /**
     * POST /drafts/{draftId}/submit-review — Submit draft for senior review.
     * Transitions status: DRAFT or REJECTED → IN_REVIEW.
     */
    @PostMapping("/{draftId}/submit-review")
    @Transactional
    public DraftStatusResponse submitForReview(@PathVariable String draftId) {
        Draft draft = getAndValidateDraft(draftId);

        String status = draft.getStatus().toUpperCase();
        if (!"DRAFT".equals(status) && !"REJECTED".equals(status)) {
            throw new ProblemException(400, "Bad Request",
                    "Only DRAFT or REJECTED drafts can be submitted for review");
        }

        draft.setStatus("IN_REVIEW");
        draftRepository.save(draft);

        DraftStatusResponse resp = new DraftStatusResponse();
        resp.setStatus(draft.getStatus());
        return resp;
    }

    /**
     * POST /drafts/{draftId}/approve — Approve a reviewed draft.
     * Blocks approval if any citations are unverified or stale.
     * Transitions status: IN_REVIEW → APPROVED_FOR_EXTERNAL_USE.
     */
    @PostMapping("/{draftId}/approve")
    @Transactional
    public DraftStatusResponse approveDraft(@PathVariable String draftId) {
        Draft draft = getAndValidateDraft(draftId);

        if (!"IN_REVIEW".equalsIgnoreCase(draft.getStatus())) {
            throw new ProblemException(400, "Bad Request",
                    "Only IN_REVIEW drafts can be approved");
        }

        // Block approval if there are unverified or stale citations
        List<DraftCitation> problematicCitations = draftCitationRepository
                .findByDraftIdAndVerificationStateIn(draftId,
                        List.of("unverified", "STALE_REVISION"));

        if (!problematicCitations.isEmpty()) {
            String state = problematicCitations.get(0).getVerificationState();
            throw new ProblemException(403, "Forbidden",
                    "Cannot approve draft. Contains " + state + " citations.");
        }

        draft.setStatus("APPROVED_FOR_EXTERNAL_USE");
        draftRepository.save(draft);

        DraftStatusResponse resp = new DraftStatusResponse();
        resp.setStatus(draft.getStatus());
        return resp;
    }

    // ── Job Dispatch: Export & Generate ──

    /**
     * POST /drafts/{draftId}/export — Export draft as PDF or DOCX.
     * Creates a background job for the Python Worker to process.
     * Draft must be APPROVED_FOR_EXTERNAL_USE and have no unverified citations.
     */
    @PostMapping("/{draftId}/export")
    @Transactional
    public ExportDraftResponse exportDraft(
            @PathVariable String draftId,
            @Valid @RequestBody ExportDraftRequest request,
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey) {

        Draft draft = getAndValidateDraft(draftId);
        RequestContext ctx = RequestContextHolder.get();

        // Validate format
        String format = request.getFormat();
        if (!"pdf".equals(format) && !"docx".equals(format)) {
            throw new ProblemException(400, "Bad Request",
                    "MIME Error: Only 'pdf' and 'docexx' formats are supported");
        }

        // Draft must be approved
        if (!"APPROVED_FOR_EXTERNAL_USE".equalsIgnoreCase(draft.getStatus())) {
            throw new ProblemException(403, "Forbidden",
                    "Draft must be APPROVED_FOR_EXTERNAL_USE to be exported");
        }

        // Block export if unverified citations exist
        List<DraftCitation> unverified = draftCitationRepository
                .findByDraftIdAndVerificationStateIn(draftId, List.of("unverified"));

        if (!unverified.isEmpty()) {
            throw new ProblemException(403, "Forbidden",
                    "Draft cannot be exported while containing UNVERIFIED citations");
        }

        // Enqueue export job for the Python Worker
        Job job = new Job();
        job.setType("EXPORT_DRAFT");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(draft.getMatterId());
        job.setRequestedBy(ctx.principalId());
        if (idempotencyKey != null) {
            job.setIdempotencyKey("export:" + draft.getId() + ":" + idempotencyKey);
        }
        job.setPayload("{\"draft_id\":\"" + draftId
                + "\",\"format\":\"" + format
                + "\",\"matter_id\":\"" + draft.getMatterId() + "\"}");
        jobRepository.save(job);

        ExportDraftResponse resp = new ExportDraftResponse();
        resp.setMessage("Export job queued");
        resp.setJobId(job.getId());
        resp.setFormat(format);
        resp.setVersion(draft.getVersion());
        return resp;
    }

    /**
     * POST /drafts/generate — Generate a draft using AI (RAG + LLM).
     * Creates a background job for the Python Worker to process.
     * The actual LLM work happens in the Python Worker's GENERATE_DRAFT handler.
     */
    @PostMapping("/generate")
    @ResponseStatus(HttpStatus.ACCEPTED)
    @Transactional
    public GenerateDraftResponse generateDraft(
            @Valid @RequestBody GenerateDraftRequest request) {

        RequestContext ctx = RequestContextHolder.get();

        // Enqueue generation job for the Python Worker
        Job job = new Job();
        job.setType("GENERATE_DRAFT");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(request.getMatterId());
        job.setRequestedBy(ctx.principalId());

        String templateName = request.getTemplateName() != null
                ? request.getTemplateName()
                : "default";
        job.setPayload("{\"tenant_id\":\"" + ctx.tenantId()
                + "\",\"matter_id\":\"" + request.getMatterId()
                + "\",\"template_name\":\"" + templateName + "\"}");
        jobRepository.save(job);

        GenerateDraftResponse resp = new GenerateDraftResponse();
        resp.setMessage("Draft generation job queued");
        resp.setJobId(job.getId());
        return resp;
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
        resp.setStatus(d.getStatus());
        return resp;
    }
}
