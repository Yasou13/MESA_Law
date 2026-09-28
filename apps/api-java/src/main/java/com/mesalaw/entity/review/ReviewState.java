package com.mesalaw.entity.review;

/**
 * Review lifecycle states for human-AI review loop.
 * Replaces Python's {@code ReviewState} from models/review.py.
 */
public enum ReviewState {
    PROPOSED,
    APPROVED,
    CORRECTED,
    REJECTED,
    PUBLISHING,
    PUBLISHED,
    PUBLICATION_FAILED
}
