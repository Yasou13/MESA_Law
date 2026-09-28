package com.mesalaw.entity.auth;

/**
 * User roles within a firm. Maps to Python's {@code Role} enum in models/domain.py.
 *
 * <p>Stored as string in the database (not native PostgreSQL enum)
 * to match the Python schema: {@code SQLEnum(Role, native_enum=False, length=50)}</p>
 */
public enum Role {
    FIRM_ADMIN,
    ATTORNEY,
    PARALEGAL,
    READ_ONLY,
    AUDITOR,
    SUPPORT_TEMPORARY
}
