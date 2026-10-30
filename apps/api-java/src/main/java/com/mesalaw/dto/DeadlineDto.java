package com.mesalaw.dto;

import java.time.LocalDate;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.mesalaw.entity.deadline.ApprovedDeadline;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO classes for Deadline endpoints.
 * Replaces Python's DeadlineResponse from routers/deadlines.py.
 */
public final class DeadlineDto {

    private DeadlineDto() {
    }

    @Data
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Response {
        private String id;
        private String matterId;
        private LocalDate dueDate;
        private String description;

        /** Python contract field name is {@code is_completed}. */
        @JsonProperty("is_completed")
        private boolean completed;

        public static Response from(ApprovedDeadline d) {
            return Response.builder()
                    .id(d.getId())
                    .matterId(d.getMatterId())
                    .dueDate(d.getDueDate())
                    .description(d.getDescription())
                    .completed(d.isCompleted())
                    .build();
        }
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class CompleteResponse {
        private String status;
    }
}
