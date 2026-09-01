package com.packsure.backend.exception;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;
import java.util.Map;

/**
 * Consistent error body for all API failures:
 * <pre>{ "timestamp", "status", "error", "message", "fieldErrors"? }</pre>
 * {@code fieldErrors} is only present for validation failures.
 */
@Getter
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ErrorResponse {
    private final Instant timestamp;
    private final int status;
    private final String error;
    private final String message;
    private final Map<String, String> fieldErrors;
}
