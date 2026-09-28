package com.mesalaw.exception;

import lombok.Getter;

/**
 * RFC 7807 Problem Details exception.
 * Replaces Python's {@code ProblemException} from core/errors.py.
 *
 * <p>Thrown by policy enforcement and business logic to return structured error responses.</p>
 */
@Getter
public class ProblemException extends RuntimeException {

    private final int status;
    private final String title;
    private final String detail;

    public ProblemException(int status, String title, String detail) {
        super(detail);
        this.status = status;
        this.title = title;
        this.detail = detail;
    }

    public ProblemException(int status, String title, String detail, Throwable cause) {
        super(detail, cause);
        this.status = status;
        this.title = title;
        this.detail = detail;
    }
}
