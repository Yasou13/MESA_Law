package com.mesalaw.entity.matter;

import java.time.OffsetDateTime;

import com.mesalaw.entity.base.TenantAwareEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * A significant event in the timeline of a matter.
 * Replaces Python's {@code MatterEvent} from models/domain.py.
 */
@Entity
@Table(name = "matter_events")
@Getter
@Setter
@NoArgsConstructor
public class MatterEvent extends TenantAwareEntity {

    @Column(name = "matter_id", nullable = false)
    private String matterId;

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @Column(name = "description")
    private String description;

    @Column(name = "event_date", nullable = false)
    private OffsetDateTime eventDate;

    @Column(name = "date_precision", nullable = false)
    private String datePrecision = "day";

    @Column(name = "source_locator_id")
    private String sourceLocatorId;

    @Column(name = "review_state", nullable = false)
    private String reviewState = "approved";

    @Column(name = "source_type", nullable = false)
    private String sourceType = "document";

    @Column(name = "confidence")
    private String confidence = "high";
}
