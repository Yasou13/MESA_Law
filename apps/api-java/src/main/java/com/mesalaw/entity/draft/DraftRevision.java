package com.mesalaw.entity.draft;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Snapshot of a draft at a specific version.
 * Replaces Python's {@code DraftRevision} from models/draft.py.
 */
@Entity
@Table(name = "draft_revisions")
@Getter
@Setter
@NoArgsConstructor
public class DraftRevision extends TenantAwareEntity {

    @Column(name = "draft_id", nullable = false)
    private String draftId;

    @Column(name = "version", nullable = false)
    private int version;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "change_summary")
    private String changeSummary;
}
