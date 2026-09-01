package com.packsure.backend.scan.dto;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.ScanStatus;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.UUID;

/** One row in the paginated {@code GET /api/scans} list. */
@Data
@Builder
public class ScanSummaryResponse {
    private UUID id;
    private String productName;
    private ScanStatus status;
    private ComplianceStatus overallStatus;
    private LocalDateTime createdAt;
}
