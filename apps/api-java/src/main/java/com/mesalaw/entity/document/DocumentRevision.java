package com.mesalaw.entity.document;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A specific revision (version) of a document with chain-of-custody metadata.
 * Replaces Python's {@code DocumentRevision} from models/document.py.
 */
@Entity
@Table(name = "document_revisions")
@Getter
@Setter
@NoArgsConstructor
public class DocumentRevision extends TenantAwareEntity {

    @Column(name = "document_id", nullable = false)
    private String documentId;

    @Column(name = "version", nullable = false)
    private int version = 1;

    @Column(name = "quarantine_key", unique = true)
    private String quarantineKey;

    @Column(name = "s3_key", unique = true)
    private String s3Key;

    @Column(name = "is_canonical", nullable = false)
    private boolean canonical = false;

    @Column(name = "immutable_at")
    private OffsetDateTime immutableAt;

    @Column(name = "failure_reason")
    private String failureReason;

    // Chain of Custody
    @Column(name = "file_hash", length = 64)
    private String fileHash;

    @Column(name = "size_bytes")
    private Integer sizeBytes;

    @Column(name = "mime_type", nullable = false)
    private String mimeType;

    @Enumerated(EnumType.STRING)
    @Column(name = "scan_status", nullable = false, length = 50)
    private DocumentState scanStatus = DocumentState.UPLOAD_INTENT_CREATED;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "document_id", insertable = false, updatable = false)
    private Document document;
}
