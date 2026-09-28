package com.mesalaw.entity.auth;

import com.mesalaw.entity.base.BaseEntity;

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
 * Links a User to a Firm with a specific Role.
 * Replaces Python's {@code Membership} from models/domain.py.
 *
 * <p>A user can have memberships in multiple firms.
 * The active firm context is resolved from the request (cookie or first active membership).</p>
 */
@Entity
@Table(name = "memberships")
@Getter
@Setter
@NoArgsConstructor
public class Membership extends BaseEntity {

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "firm_id", nullable = false)
    private String firmId;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 50)
    private Role role = Role.READ_ONLY;

    @Column(name = "is_active", nullable = false)
    private boolean active = true;

    // ── Relationships ──

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", insertable = false, updatable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "firm_id", insertable = false, updatable = false)
    private Firm firm;
}
