package com.mesalaw.entity.document;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A single page of a parsed document with text content and optional layout data.
 * Replaces Python's {@code ParsedPage} from models/parser.py.
 *
 * <p>Note: The {@code fts_vector} (TSVECTOR) column is managed by PostgreSQL triggers
 * and is not mapped as a JPA field. Queries using FTS should use native SQL.</p>
 */
@Entity
@Table(name = "parsed_pages")
@Getter
@Setter
@NoArgsConstructor
public class ParsedPage extends BaseEntity {

    @Column(name = "parsed_document_id", nullable = false)
    private String parsedDocumentId;

    @Column(name = "page_number", nullable = false)
    private int pageNumber;

    @Column(name = "text_content", nullable = false, columnDefinition = "TEXT")
    private String textContent;

    // layout_data is JSON — stored as String, parsed by service layer
    @Column(name = "layout_data", columnDefinition = "jsonb")
    private String layoutData;

    // fts_vector is managed by PostgreSQL — not mapped here

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parsed_document_id", insertable = false, updatable = false)
    private ParsedDocument parsedDocument;
}
