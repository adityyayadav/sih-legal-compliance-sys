package com.packsure.backend.scan.dto;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.ScanStatus;
import lombok.Builder;
import lombok.Data;

import java.util.UUID;

/**
 * Lightweight scan state — returned by {@code POST /api/scans} and polled via
 * {@code GET /api/scans/{id}/status}. The rich nested view is a separate endpoint.
 */
@Data
@Builder
public class ScanStatusResponse {
    private UUID id;
    private ScanStatus status;
    private ComplianceStatus overallStatus;
    private String errorMessage;
}
