package com.mesalaw.entity.auth;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * System user, linked to Keycloak via {@code keycloak_id}.
 * Replaces Python's {@code User} from models/domain.py.
 */
@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
public class User extends BaseEntity {

    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @Column(name = "keycloak_id", nullable = false, unique = true)
    private String keycloakId;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "is_support_access_granted", nullable = false)
    private boolean supportAccessGranted = false;

    @Column(name = "support_access_granted_until")
    private OffsetDateTime supportAccessGrantedUntil;
}
