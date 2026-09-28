package com.mesalaw.entity.draft;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * AI-assisted legal document draft with Tiptap editor content.
 * Replaces Python's {@code Draft} from models/draft.py.
 */
@Entity
@Table(name = "drafts")
@Getter
@Setter
@NoArgsConstructor
public class Draft extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "version", nullable = false)
    private int version = 1;

    @Column(name = "etag", nullable = false)
    private String etag = "v1";

    @Column(name = "status", nullable = false)
    private String status = "draft";
}
