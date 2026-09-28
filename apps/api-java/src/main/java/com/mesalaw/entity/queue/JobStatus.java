package com.mesalaw.entity.queue;

/**
 * Job processing status.
 * Replaces Python's {@code JobStatus} from models/queue.py.
 */
public enum JobStatus {
    PENDING,
    RUNNING,
    SUCCEEDED,
    FAILED,
    DEAD
}
