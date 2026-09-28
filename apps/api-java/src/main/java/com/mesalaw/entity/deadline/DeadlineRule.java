package com.mesalaw.entity.deadline;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A legal deadline computation rule (e.g. "15 days after notification under HMK Art. 127").
 * Replaces Python's {@code DeadlineRule} from models/deadline.py.
 */
@Entity
@Table(name = "deadline_rules")
@Getter
@Setter
@NoArgsConstructor
public class DeadlineRule extends TenantAwareEntity {

    @Column(name = "rule_name", nullable = false)
    private String ruleName;

    @Column(name = "description")
    private String description;

    @Column(name = "jurisdiction")
    private String jurisdiction;

    @Column(name = "procedure_type")
    private String procedureType;

    @Column(name = "trigger_type", nullable = false)
    private String triggerType;

    @Column(name = "duration", nullable = false)
    private int duration;

    @Column(name = "duration_unit", nullable = false)
    private String durationUnit = "days";

    @Column(name = "calculation_method", nullable = false)
    private String calculationMethod = "calendar_days";

    @Column(name = "effective_from")
    private OffsetDateTime effectiveFrom;

    @Column(name = "effective_to")
    private OffsetDateTime effectiveTo;

    @Column(name = "legal_source_id")
    private String legalSourceId;

    @Column(name = "holiday_calendar_version")
    private String holidayCalendarVersion;

    @Column(name = "reviewed_by")
    private String reviewedBy;

    @Column(name = "rule_pack_version")
    private String rulePackVersion;
}
