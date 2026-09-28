package com.mesalaw.entity.matter;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Links a user to a matter with an access scope (read, write, admin).
 * Replaces Python's {@code MatterMember} from models/domain.py.
 *
 * <p>Used by the policy engine to enforce matter-level authorization.</p>
 */
@Entity
@Table(name = "matter_members")
@Getter
@Setter
@NoArgsConstructor
public class MatterMember extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "user_id", nullable = false)
    private String userId;

    /**
     * Access scope: "read", "write", or "admin".
     */
    @Column(name = "access_scope", nullable = false)
    private String accessScope = "read";
}
