package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.ReviewDto.ApproveRequest;
import com.mesalaw.dto.ReviewDto.CorrectRequest;
import com.mesalaw.dto.ReviewDto.MutationResponse;
import com.mesalaw.dto.ReviewDto.RejectRequest;
import com.mesalaw.dto.ReviewDto.ReviewItemResponse;
import com.mesalaw.entity.review.ReviewItem;
import com.mesalaw.entity.review.ReviewState;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.ReviewItemRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

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

    private final ReviewItemRepository reviewItemRepository;

    // ── Endpoints ──

    /**
     * GET /reviews/matters/{matterId} — List review items for a matter.
     * Matches Python: GET /reviews/matters/{matter_id} → listReviewItems
     */
    @GetMapping("/matters/{matterId}")
    public List<ReviewItemResponse> listReviewItems(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<ReviewItem> items = reviewItemRepository
                .findByTenantIdAndMatterIdOrderByCreatedAtDesc(ctx.tenantId(), matterId);

        return items.stream().map(this::toResponse).collect(Collectors.toList());
    }

    /**
     * GET /reviews/{reviewId} — Get a single review item.
     */
    @GetMapping("/{reviewId}")
    public ReviewItemResponse getReviewItem(@PathVariable String reviewId) {
        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = reviewItemRepository.findById(reviewId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Review item not found"));

        if (!item.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Review item not found");
        }
        return toResponse(item);
    }

    /**
     * POST /reviews/{reviewId}/approve — Approve an AI suggestion.
     * Matches Python: POST /reviews/{review_id}/approve
     */
    @PostMapping("/{reviewId}/approve")
    public MutationResponse approveReview(
            @PathVariable String reviewId,
            @Valid @RequestBody ApproveRequest request) {

        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        item.setStatus(ReviewState.APPROVED);
        item.setReviewedBy(RequestContextHolder.get().principalId());
        item.setReviewedAt(OffsetDateTime.now());
        item.setDecisionReason(request.getReason());
        reviewItemRepository.save(item);

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId());
    }

    /**
     * POST /reviews/{reviewId}/reject — Reject an AI suggestion.
     * Matches Python: POST /reviews/{review_id}/reject
     */
    @PostMapping("/{reviewId}/reject")
    public MutationResponse rejectReview(
            @PathVariable String reviewId,
            @Valid @RequestBody RejectRequest request) {

        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        item.setStatus(ReviewState.REJECTED);
        item.setReviewedBy(RequestContextHolder.get().principalId());
        item.setReviewedAt(OffsetDateTime.now());
        item.setDecisionReason(request.getReason());
        reviewItemRepository.save(item);

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId());
    }

    /**
     * POST /reviews/{reviewId}/correct — Correct an AI suggestion with new content.
     * Matches Python: POST /reviews/{review_id}/correct
     */
    @PostMapping("/{reviewId}/correct")
    public MutationResponse correctReview(
            @PathVariable String reviewId,
            @Valid @RequestBody CorrectRequest request) {

        ReviewItem item = getAndValidateItem(reviewId, request.getExpectedVersion());
        item.setStatus(ReviewState.CORRECTED);
        item.setReviewedBy(RequestContextHolder.get().principalId());
        item.setReviewedAt(OffsetDateTime.now());
        item.setDecisionReason(request.getReason());
        item.setCorrectedContent(request.getCorrectedContent());
        reviewItemRepository.save(item);

        return new MutationResponse(item.getId(), item.getStatus(), item.getVersionId());
    }

    // ── Helpers ──

    private ReviewItem getAndValidateItem(String reviewId, int expectedVersion) {
        RequestContext ctx = RequestContextHolder.get();
        ReviewItem item = reviewItemRepository.findById(reviewId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Review item not found"));

        if (!item.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Review item not found");
        }
        if (item.getVersionId() != expectedVersion) {
            throw new ProblemException(409, "Conflict",
                    "Version mismatch: expected " + expectedVersion + ", current " + item.getVersionId());
        }
        if (item.getStatus() != ReviewState.PROPOSED) {
            throw new ProblemException(409, "Conflict", "Review item is not in PROPOSED state");
        }
        return item;
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
