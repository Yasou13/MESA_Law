package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A party in a legal matter (plaintiff, defendant, etc.).
 * Replaces Python's {@code MatterParty} from models/domain.py.
 */
@Entity
@Table(name = "matter_parties")
@Getter
@Setter
@NoArgsConstructor
public class MatterParty extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "name", nullable = false)
    private String name;

    /** e.g. PLAINTIFF, DEFENDANT, INTERVENER */
    @Column(name = "role", nullable = false)
    private String role;

    /** e.g. PERSON, ORGANIZATION */
    @Column(name = "type", nullable = false)
    private String type;

    @Column(name = "source_locator_id")
    private String sourceLocatorId;
}
