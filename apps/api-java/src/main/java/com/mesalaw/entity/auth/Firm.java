package com.mesalaw.entity.auth;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Law firm entity. Root of the multi-tenant hierarchy.
 * Replaces Python's {@code Firm} from models/domain.py.
 *
 * <p>Every tenant-aware entity references a firm via {@code tenant_id}.</p>
 */
@Entity
@Table(name = "firms")
@Getter
@Setter
@NoArgsConstructor
public class Firm extends BaseEntity {

    @Column(name = "name", nullable = false)
    private String name;

    public Firm(String id, String name) {
        this.setId(id);
        this.name = name;
    }
}
