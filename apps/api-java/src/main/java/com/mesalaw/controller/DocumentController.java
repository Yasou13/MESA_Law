package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

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
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
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

    // ── DTOs ──

    @Data
    public static class UploadIntentRequest {
        @NotBlank private String matterId;
        @NotBlank @Size(max = 255) private String filename;
        @NotBlank @Size(max = 100) private String mimeType;
        @Min(1) @Max(104857600) private long sizeBytes;
    }

    @Data
    public static class UploadIntentResponse {
        private String documentId;
        private String revisionId;
        private String presignedUrl;
        private String storageKey;

        public UploadIntentResponse(String documentId, String revisionId, String presignedUrl, String storageKey) {
            this.documentId = documentId;
            this.revisionId = revisionId;
            this.presignedUrl = presignedUrl;
            this.storageKey = storageKey;
        }
    }

    @Data
    public static class DocumentResponse {
        private String id;
        private String matterId;
        private String title;
        private String status;
        private String latestRevisionId;
        private String provenanceState;
        private String failureReason;
        private OffsetDateTime createdAt;
    }

    // ── Endpoints ──

    /**
     * POST /documents/upload-intent — Create upload intent with presigned URL.
     * Matches Python: POST /documents/upload-intent → createUploadIntent
     */
    @PostMapping("/upload-intent")
    public UploadIntentResponse createUploadIntent(@Valid @RequestBody UploadIntentRequest request) {
        RequestContext ctx = RequestContextHolder.get();

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

        return new UploadIntentResponse(doc.getId(), rev.getId(), presignedUrl, quarantineKey);
    }

    /**
     * GET /documents — List all documents the user has access to.
     * Matches Python: GET /documents → listAllDocuments
     */
    @GetMapping
    public List<DocumentResponse> listAllDocuments() {
        RequestContext ctx = RequestContextHolder.get();
        // Simplified: RLS handles tenant filtering
        List<Document> docs = documentRepository.findByMatterIdAndDeletedFalse(null);
        // For now, return empty list — real implementation needs matter member join
        return new ArrayList<>();
    }

    /**
     * GET /documents/matters/{matterId} — List documents for a specific matter.
     * Matches Python: GET /documents/matters/{matter_id} → listMatterDocuments
     */
    @GetMapping("/matters/{matterId}")
    public List<DocumentResponse> listMatterDocuments(@PathVariable String matterId) {
        RequestContext ctx = RequestContextHolder.get();
        List<Document> docs = documentRepository.findByMatterIdAndDeletedFalse(matterId);

        return docs.stream().map(d -> {
            List<DocumentRevision> revs = documentRevisionRepository
                    .findByDocumentIdOrderByVersionDesc(d.getId());
            DocumentRevision latestRev = revs.isEmpty() ? null : revs.get(0);
            return toResponse(d, latestRev);
        }).toList();
    }

    /**
     * GET /documents/{documentId} — Get a single document.
     * Matches Python: GET /documents/{document_id} → getDocument
     */
    @GetMapping("/{documentId}")
    public DocumentResponse getDocument(@PathVariable String documentId) {
        RequestContext ctx = RequestContextHolder.get();
        Document doc = documentRepository.findById(documentId)
                .orElseThrow(() -> new ProblemException(404, "Not Found", "Document not found"));

        if (!doc.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdOrderByVersionDesc(doc.getId());
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

        if (!doc.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdOrderByVersionDesc(doc.getId());
        if (revs.isEmpty()) {
            throw new ProblemException(404, "Not Found", "Revision not found");
        }

        DocumentRevision rev = revs.get(0);
        if (rev.getScanStatus() == DocumentState.UPLOADING) {
            // TODO: Verify file in storage, compute hash, create scan job
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

        if (!doc.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Document not found");
        }

        List<DocumentRevision> revs = documentRevisionRepository
                .findByDocumentIdOrderByVersionDesc(doc.getId());
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

    private DocumentResponse toResponse(Document doc, DocumentRevision rev) {
        DocumentResponse resp = new DocumentResponse();
        resp.setId(doc.getId());
        resp.setMatterId(doc.getMatterId());
        resp.setTitle(doc.getTitle());
        resp.setStatus(rev != null ? rev.getScanStatus().name() : "NO_REVISION");
        resp.setLatestRevisionId(rev != null ? rev.getId() : null);
        resp.setFailureReason(rev != null ? rev.getFailureReason() : null);
        resp.setCreatedAt(doc.getCreatedAt());

        if (rev != null && rev.getScanStatus() == DocumentState.READY) {
            resp.setProvenanceState("application/pdf".equals(rev.getMimeType())
                    ? "VERIFIED_PDF" : "LOW_PROVENANCE");
        } else {
            resp.setProvenanceState("PENDING_VERIFICATION");
        }
        return resp;
    }
}
