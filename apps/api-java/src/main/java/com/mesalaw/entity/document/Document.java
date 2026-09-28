package com.mesalaw.entity.document;

import java.util.List;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Uploaded document within a matter.
 * Replaces Python's {@code Document} from models/document.py.
 */
@Entity
@Table(name = "documents")
@Getter
@Setter
@NoArgsConstructor
public class Document extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "title", nullable = false)
    private String title;

    @OneToMany(mappedBy = "document", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<DocumentRevision> revisions;
}
