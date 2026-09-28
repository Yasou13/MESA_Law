package com.mesalaw.entity.deadline;

import java.time.LocalDate;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * An attorney-approved deadline that is tracked on the calendar.
 * Replaces Python's {@code ApprovedDeadline} from models/deadline.py.
 */
@Entity
@Table(name = "approved_deadlines")
@Getter
@Setter
@NoArgsConstructor
public class ApprovedDeadline extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "deadline_candidate_id", nullable = false)
    private String deadlineCandidateId;

    @Column(name = "due_date", nullable = false)
    private LocalDate dueDate;

    @Column(name = "timezone", nullable = false)
    private String timezone = "Europe/Istanbul";

    @Column(name = "description", nullable = false)
    private String description;

    @Column(name = "is_completed", nullable = false)
    private boolean completed = false;
}
