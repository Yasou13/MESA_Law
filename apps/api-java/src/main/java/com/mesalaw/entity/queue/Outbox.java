package com.mesalaw.entity.queue;

import com.mesalaw.entity.base.BaseEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Outbox pattern for reliable event publishing.
 * Replaces Python's {@code Outbox} from models/queue.py.
 */
@Entity
@Table(name = "legal_outbox")
@Getter
@Setter
@NoArgsConstructor
public class Outbox extends BaseEntity {

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private String payload;

    @Column(name = "status")
    private String status = "pending";
}
