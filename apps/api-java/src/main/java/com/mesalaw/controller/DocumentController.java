package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.document.Document;
import com.mesalaw.entity.document.DocumentRevision;
import com.mesalaw.entity.document.DocumentState;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.repository.DocumentRepository;
import com.mesalaw.repository.DocumentRevisionRepository;
import com.mesalaw.repository.MatterMemberRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import com.mesalaw.dto.DocumentDto;

import jakarta.transaction.Transactional;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * Document management endpoints — upload intent, complete, download, list.
 * Replaces Python's routers/documents.py.
 */
@RestController
@RequestMapping("/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final DocumentRepository documentRepository;
    private final DocumentRevisionRepository documentRevisionRepository;
    private final MatterMemberRepository matterMemberRepository;

    private static final Set<String> DOCUMENT_LIST_ROLES = Set.of(
            "FIRM_ADMIN", "ATTORNEY", "PARALEGAL", "READ_ONLY", "AUDITOR");

    // ── Endpoints ──

    /**
     * POST /documents/upload-intent — Create upload intent with presigned URL.
     * Matches Python: POST /documents/upload-intent → createUploadIntent
     */
    @PostMapping("/upload-intent")
    @Transactional
    public DocumentDto.UploadIntentResponse createUploadIntent(
            @Valid @RequestBody DocumentDto.UploadIntentRequest request) {
        RequestContext ctx = RequestContextHolder.get();
        requireMatterAccess(ctx, request.getMatterId(), true);

        // Validate MIME type
        var allowedMimes = List.of("application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain");
        if (!allowedMimes.contains(request.getMimeType())) {
            throw new ProblemException(400, "Bad Request", "Unsupported file type: " + request.getMimeType());
        }

        // Create document
        Document doc = new Document();
        doc.setTenantId(ctx.tenantId());
        doc.setMatterId(request.getMatterId());
        doc.setTitle(request.getFilename());
        documentRepository.save(doc);

        // Create provisional revision
        DocumentRevision rev = new DocumentRevision();
        rev.setTenantId(ctx.tenantId());
        rev.setDocumentId(doc.getId());
        rev.setVersion(1);
        rev.setSizeBytes((int) request.getSizeBytes());
        rev.setMimeType(request.getMimeType());
        rev.setScanStatus(DocumentState.UPLOADING);
        documentRevisionRepository.save(rev);

        // Generate quarantine key
        String ext = switch (request.getMimeType()) {
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document" -> ".docx";
            case "text/plain" -> ".txt";
            default -> ".pdf";
        };
        String quarantineKey = "quarantine/" + ctx.tenantId() + "/" + request.getMatterId() + "/" + rev.getId() + ext;
        rev.setQuarantineKey(quarantineKey);
        documentRevisionRepository.save(rev);

        // TODO: Generate actual presigned URL via S3/MinIO service
        String presignedUrl = "https://storage.example.com/upload?key=" + quarantineKey;

        return new DocumentDto.UploadIntentResponse(doc.getId(), rev.getId(), presignedUrl, quarantineKey);
    }

    /**
     * GET /documents — List all documents the user has access to.
     * Matches Python: GET /documents → listAllDocuments
     */
    @GetMapping
    public List<DocumentDto.DocumentResponse> listAllDocuments() {
        RequestContext ctx = RequestContextHolder.get();
        if (!ctx.hasAnyRole(DOCUMENT_LIST_ROLES)) {
            throw new ProblemException(403, "Forbidden", "Requires one of scopes: list assigned matters");
        }

        List<Document> docs = documentRepository.findAccessibleDocuments(ctx.tenantId(), ctx.principalId());

        return docs.stream().map(d -> {
            List<DocumentRevision> revs = documentRevisionRepository
                    .findByDocumentIdAndTenantIdOrderByVersionDesc(d.getId(), ctx.tenantId());
            DocumentRevision latestRev = revs.isEmpty() ? null : revs.get(0);
            return toResponse(d, latestRev);
        }).toList();
    }

    /**
     * GET /documents/matters/{matterId} — List documents for a specific matter.
     * Matches Python: GET /documents/matters/{matter_id} → listMatterDocuments
     */
    @GetMapping("/matters/{matterId}")
    public List<DocumentDto.DocumentResponse> listMatterDocuments(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        requireMatterAccess(ctx, matterId, false);
        List<Document> docs = documentRepository.findByMatterIdAndTenantIdAndDeletedFalse(matterId, ctx.tenantId());

        return docs.stream().map(d -> {
            List<DocumentRevision> revs = documentRevisionRepository
                    .findByDocumentIdAndTenantIdOrderByVersionDesc(d.getId(), ctx.tenantId());
            DocumentRevision latestRev = revs.isEmpty() ? null : revs.get(0);
            return toResponse(d, latestRev);
        }).toList();
    }

    /**
     * GET /documents/{documentId} — Get a single document.
     * Matches Python: GET /documents/{document_id} → getDocument
     */
    @GetMapping("/{documentId}")
    public DocumentDto.DocumentResponse getDocument(@PathVariable String documentId) {
        RequestContext ctx = RequestContextHolder.get();
        Document doc = documentRepository.findById(documentId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Document not found"));

        if (!doc.getTenantId().equals(ctx.tenantId()) || doc.isDeleted()) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }
        requireMatterAccess(ctx, doc.getMatterId(), false);

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdAndTenantIdOrderByVersionDesc(doc.getId(), ctx.tenantId());
        DocumentRevision latestRev = revs.isEmpty() ? null : revs.get(0);
        return toResponse(doc, latestRev);
    }

    /**
     * POST /documents/{documentId}/complete — Confirm upload completed.
     * Matches Python: POST /documents/{document_id}/complete → completeUpload
     */
    @PostMapping("/{documentId}/complete")
    public Map<String, String> completeUpload(@PathVariable String documentId) {
        RequestContext ctx = RequestContextHolder.get();
        Document doc = documentRepository.findById(documentId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Document not found"));

        if (!doc.getTenantId().equals(ctx.tenantId()) || doc.isDeleted()) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }
        requireMatterAccess(ctx, doc.getMatterId(), true);

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdAndTenantIdOrderByVersionDesc(doc.getId(), ctx.tenantId());
        if (revs.isEmpty()) {
            throw new ProblemException(404, "Not Found", "Revision not found");
        }

        DocumentRevision rev = revs.get(0);
        if (rev.getScanStatus() == DocumentState.UPLOADING) {
            if (rev.getQuarantineKey() == null || rev.isCanonical()) {
                throw new ProblemException(409, "Conflict", "Invalid upload revision state");
            }
            if (rev.getSizeBytes() == null || rev.getSizeBytes() < 1 || rev.getSizeBytes() > 104857600) {
                throw new ProblemException(400, "Bad Request", "Invalid upload size");
            }
            // Storage verification and scan job creation require the planned MinIO
            // integration.
            rev.setScanStatus(DocumentState.SCANNING);
            documentRevisionRepository.save(rev);
        }

        return Map.of("status", rev.getScanStatus().name(), "revision_id", rev.getId());
    }

    /**
     * GET /documents/{documentId}/download — Get presigned download URL.
     * Matches Python: GET /documents/{document_id}/download → downloadDocument
     */
    @GetMapping("/{documentId}/download")
    public Map<String, Object> downloadDocument(@PathVariable String documentId) {
        RequestContext ctx = RequestContextHolder.get();
        Document doc = documentRepository.findById(documentId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Document not found"));

        if (!doc.getTenantId().equals(ctx.tenantId()) || doc.isDeleted()) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }
        requireMatterAccess(ctx, doc.getMatterId(), false);

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdAndTenantIdOrderByVersionDesc(doc.getId(), ctx.tenantId());
        if (revs.isEmpty()) {
            throw new ProblemException(404, "Not Found", "Revision not found");
        }

        DocumentRevision rev = revs.get(0);
        if (rev.getScanStatus() == DocumentState.INFECTED) {
            throw new ProblemException(403, "Forbidden", "Document is infected and cannot be downloaded");
        }
        if (!rev.isCanonical() || rev.getS3Key() == null) {
            throw new ProblemException(425, "Too Early", "Document is still being scanned");
        }

        // TODO: Generate actual presigned download URL via S3/MinIO service
        String url = "https://storage.example.com/download?key=" + rev.getS3Key();
        return Map.of("presigned_url", url, "expires_in_seconds", 300);
    }

    private DocumentDto.DocumentResponse toResponse(Document doc, DocumentRevision rev) {
        DocumentDto.DocumentResponse resp = new DocumentDto.DocumentResponse();
        resp.setId(doc.getId());
        resp.setMatterId(doc.getMatterId());
        resp.setTitle(doc.getTitle());
        resp.setStatus(rev != null ? rev.getScanStatus().name() : "NO_REVISION");
        resp.setLatestRevisionId(rev != null ? rev.getId() : null);
        resp.setFailureReason(rev != null ? rev.getFailureReason() : null);
        resp.setCreatedAt(doc.getCreatedAt());

        if (rev != null && rev.getScanStatus() == DocumentState.READY) {
            resp.setProvenanceState("application/pdf".equals(rev.getMimeType())
                    ? "VERIFIED_PDF"
                    : "LOW_PROVENANCE");
        } else {
            resp.setProvenanceState("PENDING_VERIFICATION");
        }
        return resp;
    }

    private void requireMatterAccess(RequestContext ctx, String matterId, boolean write) {
        Set<String> allowedRoles = write
                ? Set.of("FIRM_ADMIN", "ATTORNEY", "PARALEGAL")
                : DOCUMENT_LIST_ROLES;
        if (!ctx.hasAnyRole(allowedRoles)) {
            throw new ProblemException(403, "Forbidden", write
                    ? "You do not have permission to upload documents"
                    : "You do not have permission to read documents");
        }

        var member = matterMemberRepository.findByMatterIdAndUserIdAndTenantIdAndDeletedFalse(
                matterId, ctx.principalId(), ctx.tenantId())
                .orElseThrow(() -> new ProblemException(403, "Forbidden", "You are not a member of this matter"));
        Set<String> allowedScopes = write ? Set.of("write", "admin") : Set.of("read", "write", "admin");
        if (!allowedScopes.contains(member.getAccessScope())) {
            throw new ProblemException(403, "Forbidden", "Insufficient matter access scope");
        }
    }
}
