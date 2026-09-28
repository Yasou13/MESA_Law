package com.mesalaw.entity.document;

import java.util.List;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Result of parsing a document revision.
 * Replaces Python's {@code ParsedDocument} from models/parser.py.
 */
@Entity
@Table(name = "parsed_documents", uniqueConstraints = {
        @UniqueConstraint(name = "uq_parsed_document_revision_run",
                columnNames = {"revision_id", "parsing_revision"})
})
@Getter
@Setter
@NoArgsConstructor
public class ParsedDocument extends TenantAwareEntity {

    @Column(name = "document_id", nullable = false)
    private String documentId;

    @Column(name = "revision_id", nullable = false)
    private String revisionId;

    @Column(name = "parsing_revision", nullable = false)
    private int parsingRevision = 1;

    @Column(name = "parser_used", nullable = false)
    private String parserUsed;

    @Column(name = "ocr_version")
    private String ocrVersion;

    @Column(name = "pipeline_version")
    private String pipelineVersion;

    @Column(name = "input_hash")
    private String inputHash;

    @Column(name = "output_hash")
    private String outputHash;

    @Column(name = "status", nullable = false)
    private String status = "completed";

    @Column(name = "provenance_state", nullable = false)
    private String provenanceState = "LOW_PROVENANCE";

    @OneToMany(mappedBy = "parsedDocument", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<ParsedPage> pages;
}
