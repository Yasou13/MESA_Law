package com.mesalaw.controller;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.audit.Notification;
import com.mesalaw.repository.NotificationRepository;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Notification endpoints — list and mark as read.
 * Replaces Python's routers/notifications.py.
 */
@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationRepository notificationRepository;

    @Data
    @AllArgsConstructor
    public static class NotificationResponse {
        private String id;
        private String category;
        private String title;
        private String message;
        private String status;
        private String timestamp;
    }

    /**
     * GET /notifications — List all notifications for the current user.
     * Matches Python: GET /notifications → getNotifications
     */
    @GetMapping
    public List<NotificationResponse> listNotifications() {
        RequestContext ctx = RequestContextHolder.get();
        List<Notification> notifications = notificationRepository
                .findByTenantIdAndUserIdOrderByTimestampDesc(ctx.tenantId(), ctx.principalId());

        return notifications.stream()
                .map(n -> new NotificationResponse(
                        n.getId(),
                        n.getCategory(),
                        n.getTitle(),
                        n.getMessage(),
                        n.getStatus(),
                        n.getTimestamp().toString()))
                .collect(Collectors.toList());
    }

    /**
     * POST /notifications/{notificationId}/read — Mark notification as READ.
     */
    @PostMapping("/{notificationId}/read")
    public java.util.Map<String, String> markAsRead(@PathVariable String notificationId) {
        RequestContext ctx = RequestContextHolder.get();
        Notification notification = notificationRepository.findById(notificationId)
                .orElseThrow(() -> new com.mesalaw.exception.ProblemException(
                        404, "Not Found", "Notification not found"));

        if (!notification.getTenantId().equals(ctx.tenantId()) ||
                !notification.getUserId().equals(ctx.principalId())) {
            throw new com.mesalaw.exception.ProblemException(
                    404, "Not Found", "Notification not found");
        }

        notification.setStatus("READ");
        notificationRepository.save(notification);

        return java.util.Map.of("status", "success");
    }

    // TODO: SSE endpoint for real-time notifications
    // Spring MVC SSE uses SseEmitter — will be implemented in a later phase
}
