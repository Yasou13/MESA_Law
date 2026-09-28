package com.mesalaw.entity.deadline;

/**
 * Deadline lifecycle states.
 * Replaces Python's {@code DeadlineState} from models/deadline.py.
 */
public enum DeadlineState {
    POTENTIAL_DEADLINE,
    RULE_MATCHED,
    CALCULATED,
    ATTORNEY_VERIFIED,
    SCHEDULED,
    REJECTED
}
