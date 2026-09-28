package com.mesalaw.entity.document;

/**
 * Document processing state machine.
 * Replaces Python's {@code DocumentState} from models/document.py.
 */
public enum DocumentState {
    UPLOAD_INTENT_CREATED,
    UPLOADING,
    UPLOADED,
    VERIFYING,
    QUARANTINED,
    SCANNING,
    CLEAN,
    INFECTED,
    PARSING,
    OCR_REQUIRED,
    OCR_RUNNING,
    PARSED,
    EXTRACTION_PENDING,
    READY,
    FAILED,
    BLOCKED,
    MANUAL_REVIEW_REQUIRED
}
