package com.mesalaw.entity.document;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A content-addressed chunk of a parsed page used for RAG retrieval and citations.
 * Replaces Python's {@code DocumentChunk} from models/parser.py.
 *
 * <p>Note: The {@code fts_vector} (TSVECTOR) column is managed by PostgreSQL triggers.</p>
 */
@Entity
@Table(name = "document_chunks", uniqueConstraints = {
        @UniqueConstraint(name = "uq_document_chunk_span",
                columnNames = {"revision_id", "page_id", "chunk_index"})
})
@Getter
@Setter
@NoArgsConstructor
public class DocumentChunk extends TenantAwareEntity {

    @Column(name = "document_id", nullable = false)
    private String documentId;

    @Column(name = "revision_id")
    private String revisionId;

    @Column(name = "page_id", nullable = false)
    private String pageId;

    @Column(name = "chunk_index", nullable = false)
    private int chunkIndex;

    @Column(name = "chunk_type", nullable = false)
    private String chunkType = "block";

    @Column(name = "text_content", nullable = false, columnDefinition = "TEXT")
    private String textContent;

    @Column(name = "watermarked_text", nullable = false, columnDefinition = "TEXT")
    private String watermarkedText;

    @Column(name = "character_start")
    private Integer characterStart;

    @Column(name = "character_end")
    private Integer characterEnd;

    @Column(name = "content_sha256", length = 64)
    private String contentSha256;

    @Column(name = "extraction_version")
    private String extractionVersion;

    @Column(name = "provenance_state", nullable = false)
    private String provenanceState = "LOW_PROVENANCE";

    // bbox is JSON — stored as String
    @Column(name = "bbox", columnDefinition = "jsonb")
    private String bbox;

    // fts_vector is managed by PostgreSQL — not mapped here
}
