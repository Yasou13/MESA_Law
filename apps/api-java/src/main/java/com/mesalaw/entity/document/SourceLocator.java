package com.mesalaw.entity.document;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Precise source locator pinpointing evidence to a specific page, character range, and bbox.
 * Replaces Python's {@code SourceLocator} from models/domain.py.
 *
 * <p>Central provenance entity — links assertions, claims, and evidence back to
 * exact document positions with cryptographic verification.</p>
 */
@Entity
@Table(name = "source_locators")
@Getter
@Setter
@NoArgsConstructor
public class SourceLocator extends TenantAwareEntity {

    @Column(name = "matter_id")
    private String matterId;

    @Column(name = "document_id", nullable = false)
    private String documentId;

    @Column(name = "document_revision_id")
    private String documentRevisionId;

    @Column(name = "parsed_document_id")
    private String parsedDocumentId;

    @Column(name = "parsed_page_id")
    private String parsedPageId;

    @Column(name = "chunk_id")
    private String chunkId;

    @Column(name = "page_number", nullable = false)
    private int pageNumber;

    @Column(name = "paragraph_index")
    private Integer paragraphIndex;

    @Column(name = "block_index")
    private Integer blockIndex;

    @Column(name = "character_start")
    private Integer characterStart;

    @Column(name = "character_end")
    private Integer characterEnd;

    @Column(name = "bbox_x0")
    private Double bboxX0;

    @Column(name = "bbox_y0")
    private Double bboxY0;

    @Column(name = "bbox_x1")
    private Double bboxX1;

    @Column(name = "bbox_y1")
    private Double bboxY1;

    @Column(name = "text_snippet")
    private String textSnippet;

    @Column(name = "text_hash")
    private String textHash;

    @Column(name = "evidence_text", columnDefinition = "TEXT")
    private String evidenceText;

    @Column(name = "evidence_sha256", length = 64)
    private String evidenceSha256;

    @Column(name = "parser_version")
    private String parserVersion;

    @Column(name = "ocr_version")
    private String ocrVersion;

    @Column(name = "extraction_version")
    private String extractionVersion;

    @Column(name = "provenance_state", nullable = false)
    private String provenanceState = "LOW_PROVENANCE";

    @Column(name = "verified_at")
    private OffsetDateTime verifiedAt;
}
