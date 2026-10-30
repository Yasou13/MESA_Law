package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mesalaw.dto.ReviewDto.ApproveRequest;
import com.mesalaw.dto.ReviewDto.AuditEntry;
import com.mesalaw.dto.ReviewDto.CorrectRequest;
import com.mesalaw.dto.ReviewDto.MutationResponse;
import com.mesalaw.dto.ReviewDto.RejectRequest;
import com.mesalaw.dto.ReviewDto.ReviewContextResponse;
import com.mesalaw.dto.ReviewDto.ReviewItemResponse;
import com.mesalaw.dto.ReviewDto.SourceContext;
import com.mesalaw.dto.ReviewDto.SuggestionContext;
import com.mesalaw.entity.audit.LegalAuditLog;
import com.mesalaw.entity.document.Document;
import com.mesalaw.entity.document.SourceLocator;
import com.mesalaw.entity.matter.MatterMember;
import com.mesalaw.entity.queue.Job;
import com.mesalaw.entity.review.ExtractionSuggestion;
import com.mesalaw.entity.review.ReviewItem;
import com.mesalaw.entity.review.ReviewState;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.DocumentRepository;
import com.mesalaw.repository.ExtractionSuggestionRepository;
import com.mesalaw.repository.JobRepository;
import com.mesalaw.repository.LegalAuditLogRepository;
import com.mesalaw.repository.ReviewItemRepository;
import com.mesalaw.repository.SourceLocatorRepository;
import com.mesalaw.security.MatterAccessGuard;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.criteria.Subquery;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * Review pipeline endpoints — approve, reject, correct AI suggestions.
 * Replaces Python's routers/reviews.py.
 */
@RestController
@RequestMapping("/reviews")
@RequiredArgsConstructor
public class ReviewController {

    private static final Set<String> READ_ROLES = MatterAccessGuard.READ_ROLES;
    private static final Set<String> REVIEW_DECISION_ROLES = MatterAccessGuard.REVIEW_DECISION_ROLES;
    private static final Set<String> READ_SCOPES = MatterAccessGuard.READ_SCOPES;
    private static final Set<String> WRITE_SCOPES = MatterAccessGuard.WRITE_SCOPES;
    private static final List<String> DECISION_ACTIONS = List.of(
            "APPROVE_REVIEW", "CORRECT_REVIEW", "REJECT_REVIEW");
    /** Cooling-off window before an approved/corrected item may be used externally (matches Python). */
    private static final long EXTERNAL_USE_DELAY_HOURS = 2;

    private final ReviewItemRepository reviewItemRepository;
    private final ExtractionSuggestionRepository suggestionRepository;
    private final SourceLocatorRepository sourceLocatorRepository;
    private final DocumentRepository documentRepository;
    private final LegalAuditLogRepository auditLogRepository;
    private final JobRepository jobRepository;
    private final MatterAccessGuard accessGuard;
    private final ObjectMapper objectMapper;

    // ── Endpoints ──

    /**
     * GET /reviews — List review items with optional filters.
     * Matches Python: GET /reviews → listReviews
     *
     * <p>Without {@code matterId}, only items from matters the caller is a member of are returned.</p>
     */
    @GetMapping
    @Transactional(readOnly = true)
    public List<ReviewItemResponse> listReviews(
            @RequestParam(required = false) String matterId,
            @RequestParam(required = false) ReviewState status,
            @RequestParam(required = false) String entityType) {
        RequestContext ctx = RequestContextHolder.get();
        requireRoles(ctx, READ_ROLES, "read matters");

        Specification<ReviewItem> spec = (root, query, cb) -> cb.equal(root.get("tenantId"), ctx.tenantId());

        if (matterId != null) {
            requireMatterScope(ctx, matterId, READ_SCOPES);
            spec = spec.and((root, query, cb) -> cb.equal(root.get("matterId"), matterId));
        } else {
            spec = spec.and((root, query, cb) -> {
                Subquery<String> memberMatters = query.subquery(String.class);
                var member = memberMatters.from(MatterMember.class);
                memberMatters.select(member.get("matterId")).where(
                        cb.equal(member.get("userId"), ctx.principalId()),
                        cb.equal(member.get("tenantId"), ctx.tenantId()),
                        cb.isFalse(member.get("deleted")));
                return root.get("matterId").in(memberMatters);
            });
        }
        if (status != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("status"), status));
        }
        if (entityType != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("entityType"), entityType));
        }

        return reviewItemRepository.findAll(spec, Sort.by(Sort.Direction.ASC, "createdAt"))
                .stream().map(this::toResponse).collect(Collectors.toList());
    }

    /**
     * GET /reviews/matters/{matterId} — List review items for a matter.
     * Matches Python: GET /reviews/matters/{matter_id} → listReviewItems
     */
    @GetMapping("/matters/{matterId}")
    @Transactional(readOnly = true)
    public List<ReviewItemResponse> listReviewItems(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        requireRoles(ctx, READ_ROLES, "read matters");
        requireMatterScope(ctx, matterId, READ_SCOPES);

        List<ReviewItem> items = reviewItemRepository
                .findByTenantIdAndMatterIdOrderByCreatedAtDesc(ctx.tenantId(), matterId);

        return items.stream().map(this::toResponse).collect(Collectors.toList());
    }

    /**
     * GET /reviews/{reviewId} — Get a single review item.
     */
    @GetMapping("/{reviewId}")
    @Transactional(readOnly = true)
    public ReviewItemResponse getReviewItem(@PathVariable String reviewId) {
        return toResponse(loadForRead(reviewId));
    }

    /**
     * GET /reviews/{reviewId}/context — Review item + AI suggestion metadata + source evidence + decision history.
     * Matches Python: GET /reviews/{review_id}/context → getReviewContext
     */
    @GetMapping("/{reviewId}/context")
    @Transactional(readOnly = true)
    public ReviewContextResponse getReviewContext(@PathVariable String reviewId) {
        RequestContext ctx = RequestContextHolder.get();
        ReviewItem review = loadForRead(reviewId);

        ReviewContextResponse resp = new ReviewContextResponse();
        resp.setReview(toResponse(review));

        ExtractionSuggestion suggestion = review.getSuggestionId() == null ? null
                : suggestionRepository.findByIdAndTenantIdAndMatterId(
                        review.getSuggestionId(), ctx.tenantId(), review.getMatterId()).orElse(null);

        if (suggestion != null) {
            SuggestionContext sc = new SuggestionContext();
            sc.setId(suggestion.getId());
            sc.setSuggestionType(suggestion.getSuggestionType());
            sc.setExtractorName(suggestion.getExtractorName());
            sc.setExtractorVersion(suggestion.getExtractorVersion());
            sc.setParserVersion(suggestion.getParserVersion());
            sc.setConfidenceCategory(suggestion.getConfidenceCategory());
            resp.setSuggestion(sc);

            if (suggestion.getSourceLocatorId() != null) {
                resp.setSource(buildSourceContext(ctx, review, suggestion));
            }
        }

        List<LegalAuditLog> history = auditLogRepository
                .findByTenantIdAndMatterIdAndEntityTypeAndEntityIdAndActionInOrderByCreatedAtAsc(
                        ctx.tenantId(), review.getMatterId(), review.getEntityType(),
                        review.getEntityId(), DECISION_ACTIONS);
        resp.setHistory(history.stream().map(entry -> {
            AuditEntry ae = new AuditEntry();
            ae.setId(entry.getId());
            ae.setAction(entry.getAction());
            ae.setUserId(entry.getUserId());
            ae.setCreatedAt(entry.getCreatedAt());
            ae.setDetails(entry.getDetails());
            return ae;
        }).collect(Collectors.toList()));

        return resp;
    }

    /**
     * POST /reviews/{reviewId}/approve — Approve an AI suggestion.
     * Matches Python: POST /reviews/{review_id}/approve
     */
    @PostMapping("/{reviewId}/approve")
    @Transactional
    public MutationResponse approveReview(
            @PathVariable String reviewId,
            @Valid @RequestBody ApproveRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        String before = item.getProposedContent();

        transition(ctx, item, ReviewState.APPROVED, request.getReason(), null);
        Job job = enqueuePublication(ctx, item);
        writeAudit(ctx, item, "APPROVE_REVIEW", before, before, request.getReason());

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId(), job.getId());
    }

    /**
     * POST /reviews/{reviewId}/reject — Reject an AI suggestion.
     * Matches Python: POST /reviews/{review_id}/reject
     */
    @PostMapping("/{reviewId}/reject")
    @Transactional
    public MutationResponse rejectReview(
            @PathVariable String reviewId,
            @Valid @RequestBody RejectRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        String before = item.getProposedContent();

        transition(ctx, item, ReviewState.REJECTED, request.getReason(), null);
        writeAudit(ctx, item, "REJECT_REVIEW", before, null, request.getReason());

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId());
    }

    /**
     * POST /reviews/{reviewId}/correct — Correct an AI suggestion with new content.
     * Matches Python: POST /reviews/{review_id}/correct
     */
    @PostMapping("/{reviewId}/correct")
    @Transactional
    public MutationResponse correctReview(
            @PathVariable String reviewId,
            @Valid @RequestBody CorrectRequest request) {

        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        String before = item.getProposedContent();

        transition(ctx, item, ReviewState.CORRECTED, request.getReason(), request.getCorrectedContent());
        Job job = enqueuePublication(ctx, item);
        writeAudit(ctx, item, "CORRECT_REVIEW", before, request.getCorrectedContent(), request.getReason());

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId(), job.getId());
    }

    // ── Helpers ──

    private ReviewItem getAndValidateItem(String reviewId, int expectedVersion) {
        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = reviewItemRepository.findByIdAndTenantId(reviewId, ctx.tenantId())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Review item not found"));

        // Matches Python ReviewAccessPolicy.can_approve
        requireRoles(ctx, REVIEW_DECISION_ROLES, "approve or reject AI reviews");
        requireMatterScope(ctx, item.getMatterId(), WRITE_SCOPES);

        if (item.getVersionId() != expectedVersion) {
            throw new ProblemException(409, "Conflict",
                    "Version mismatch: expected " + expectedVersion + ", current " + item.getVersionId());
        }
        if (item.getStatus() != ReviewState.PROPOSED) {
            throw new ProblemException(409, "Conflict", "Review item is not in PROPOSED state");
        }
        return item;
    }

    private ReviewItem loadForRead(String reviewId) {
        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = reviewItemRepository.findByIdAndTenantId(reviewId, ctx.tenantId())
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Review item not found"));
        requireRoles(ctx, READ_ROLES, "read matters");
        requireMatterScope(ctx, item.getMatterId(), READ_SCOPES);
        return item;
    }

    /**
     * Applies the decision, bumps the optimistic-lock version (via @Version on flush)
     * and mirrors the new state onto the originating ExtractionSuggestion.
     */
    private void transition(RequestContext ctx, ReviewItem item, ReviewState target,
                            String reason, String correctedContent) {
        OffsetDateTime now = OffsetDateTime.now();
        item.setStatus(target);
        item.setReviewedBy(ctx.principalId());
        item.setReviewedAt(now);
        item.setDecisionReason(reason);
        item.setCorrectedContent(correctedContent);
        item.setExternalUseReadyAt(target == ReviewState.REJECTED ? null : now.plusHours(EXTERNAL_USE_DELAY_HOURS));
        item.setUpdatedBy(ctx.principalId());

        try {
            reviewItemRepository.saveAndFlush(item);
        } catch (ObjectOptimisticLockingFailureException e) {
            throw new ProblemException(409, "Conflict", "Review item was modified concurrently", e);
        }

        if (item.getSuggestionId() != null) {
            suggestionRepository.findByIdAndTenantId(item.getSuggestionId(), item.getTenantId())
                    .ifPresent(s -> {
                        s.setReviewState(target.name());
                        suggestionRepository.save(s);
                    });
        }
    }

    /** Enqueues the PUBLISH_REVIEW job consumed by the Python worker (handle_publish_review). */
    private Job enqueuePublication(RequestContext ctx, ReviewItem item) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("review_id", item.getId());
        payload.put("matter_id", item.getMatterId());

        Job job = new Job();
        job.setType("PUBLISH_REVIEW");
        job.setTenantId(ctx.tenantId());
        job.setMatterId(item.getMatterId());
        job.setRequestedBy(ctx.principalId());
        job.setIdempotencyKey("publish:" + item.getId() + ":" + item.getVersionId());
        job.setPayload(toJson(payload));
        return jobRepository.save(job);
    }

    private void writeAudit(RequestContext ctx, ReviewItem item, String action,
                            String before, String after, String reason) {
        Map<String, Object> details = new LinkedHashMap<>();
        details.put("before", parseJsonOrRaw(before));
        details.put("after", parseJsonOrRaw(after));
        details.put("reason", reason);
        details.put("review_version", item.getVersionId());

        LegalAuditLog log = new LegalAuditLog();
        log.setTenantId(ctx.tenantId());
        log.setMatterId(item.getMatterId());
        log.setUserId(ctx.principalId());
        log.setAction(action);
        log.setEntityType(item.getEntityType());
        log.setEntityId(item.getEntityId());
        log.setDetails(toJson(details));
        auditLogRepository.save(log);
    }

    private SourceContext buildSourceContext(RequestContext ctx, ReviewItem review, ExtractionSuggestion suggestion) {
        SourceLocator locator = sourceLocatorRepository
                .findByIdAndTenantIdAndMatterIdAndDocumentIdAndDocumentRevisionId(
                        suggestion.getSourceLocatorId(), ctx.tenantId(), review.getMatterId(),
                        suggestion.getDocumentId(), suggestion.getDocumentRevisionId())
                .orElse(null);
        if (locator == null) {
            return null;
        }
        Document document = documentRepository.findById(locator.getDocumentId())
                .filter(d -> ctx.tenantId().equals(d.getTenantId())
                        && review.getMatterId().equals(d.getMatterId()))
                .orElse(null);
        if (document == null) {
            return null;
        }

        SourceContext src = new SourceContext();
        src.setDocumentId(document.getId());
        src.setDocumentTitle(document.getTitle());
        src.setRevisionId(suggestion.getDocumentRevisionId());
        src.setPageNumber(locator.getPageNumber());
        src.setChunkId(locator.getChunkId());
        src.setTextStart(locator.getCharacterStart());
        src.setTextEnd(locator.getCharacterEnd());
        if (locator.getBboxX0() != null && locator.getBboxY0() != null
                && locator.getBboxX1() != null && locator.getBboxY1() != null) {
            src.setBbox(Map.of(
                    "x0", locator.getBboxX0(), "y0", locator.getBboxY0(),
                    "x1", locator.getBboxX1(), "y1", locator.getBboxY1()));
        }
        src.setEvidenceText(locator.getEvidenceText() != null ? locator.getEvidenceText() : locator.getTextSnippet());
        src.setEvidenceSha256(locator.getEvidenceSha256() != null ? locator.getEvidenceSha256() : locator.getTextHash());
        src.setParserVersion(locator.getParserVersion());
        src.setExtractionVersion(locator.getExtractionVersion());
        src.setProvenanceState(locator.getProvenanceState());
        return src;
    }

    private void requireRoles(RequestContext ctx, Set<String> roles, String action) {
        accessGuard.requireRoles(ctx, roles, action);
    }

    private void requireMatterScope(RequestContext ctx, String matterId, Set<String> scopes) {
        accessGuard.requireMatterScope(ctx, matterId, scopes);
    }

    private Object parseJsonOrRaw(String value) {
        if (value == null) {
            return null;
        }
        try {
            return objectMapper.readTree(value);
        } catch (JsonProcessingException e) {
            return value;
        }
    }

    private String toJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Failed to serialize JSON", e);
        }
    }

    private ReviewItemResponse toResponse(ReviewItem item) {
        ReviewItemResponse resp = new ReviewItemResponse();
        resp.setId(item.getId());
        resp.setMatterId(item.getMatterId());
        resp.setEntityType(item.getEntityType());
        resp.setEntityId(item.getEntityId());
        resp.setProposedContent(item.getProposedContent());
        resp.setCorrectedContent(item.getCorrectedContent());
        resp.setStatus(item.getStatus());
        resp.setSuggestionId(item.getSuggestionId());
        resp.setDecisionReason(item.getDecisionReason());
        resp.setVersionId(item.getVersionId());
        return resp;
    }
}
