package com.mesalaw.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Root and health endpoints.
 * Replaces Python's root endpoint and parts of routers/system.py.
 */
@RestController
public class SystemController {

    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of(
                "status", "ok",
                "message", "MESA Law API is running"
        );
    }

    @GetMapping("/health/live")
    public Map<String, String> healthLive() {
        return Map.of("status", "ok");
    }

    @GetMapping("/health/ready")
    public Map<String, String> healthReady() {
        // TODO: Add database, Redis, MinIO connectivity checks
        return Map.of("status", "ok");
    }
}
