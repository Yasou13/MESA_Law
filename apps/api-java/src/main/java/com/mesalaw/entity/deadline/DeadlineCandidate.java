package com.mesalaw.entity.deadline;

import java.time.LocalDate;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A computed deadline candidate awaiting attorney review.
 * Replaces Python's {@code DeadlineCandidate} from models/deadline.py.
 */
@Entity
@Table(name = "deadline_candidates")
@Getter
@Setter
@NoArgsConstructor
public class DeadlineCandidate extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "rule_id", nullable = false)
    private String ruleId;

    @Column(name = "trigger_event")
    private String triggerEvent;

    @Column(name = "trigger_date")
    private LocalDate triggerDate;

    @Column(name = "calculation_trace", columnDefinition = "jsonb")
    private String calculationTrace;

    @Column(name = "calculated_date", nullable = false)
    private LocalDate calculatedDate;

    @Column(name = "description", nullable = false)
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private DeadlineState status = DeadlineState.POTENTIAL_DEADLINE;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "timezone", nullable = false)
    private String timezone = "Europe/Istanbul";
}
