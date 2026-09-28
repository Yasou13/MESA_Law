package com.mesalaw.exception;

import java.time.OffsetDateTime;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Global exception handler producing RFC 7807 Problem JSON responses.
 * Replaces Python's {@code problem_exception_handler} and {@code global_exception_handler}
 * from core/errors.py.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ProblemException.class)
    public ResponseEntity<Map<String, Object>> handleProblem(ProblemException ex, HttpServletRequest request) {
        return ResponseEntity
                .status(ex.getStatus())
                .body(problemBody(ex.getStatus(), ex.getTitle(), ex.getDetail(), request));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException ex,
                                                                HttpServletRequest request) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .reduce((a, b) -> a + "; " + b)
                .orElse("Validation failed");

        return ResponseEntity
                .status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(problemBody(422, "Validation Error", detail, request));
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDenied(AccessDeniedException ex,
                                                                  HttpServletRequest request) {
        return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(problemBody(403, "Forbidden", "You do not have permission to perform this action.", request));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneral(Exception ex, HttpServletRequest request) {
        log.error("Unhandled exception on {} {}", request.getMethod(), request.getRequestURI(), ex);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(problemBody(500, "Internal Server Error",
                        "An unexpected error occurred. Please try again later.", request));
    }

    private Map<String, Object> problemBody(int status, String title, String detail, HttpServletRequest request) {
        return Map.of(
                "type", "about:blank",
                "title", title,
                "status", status,
                "detail", detail,
                "instance", request.getRequestURI(),
                "timestamp", OffsetDateTime.now().toString()
        );
    }
}
