package com.packsure.backend.report.dto;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.ScanStatus;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/** The rich nested view behind {@code GET /api/scans/{id}/detailed}. */
@Data
@Builder
public class DetailedScanResponse {

    private ScanInfo scan;
    private ProductInfo product;
    private List<DeclarationResponse> declarations;
    private List<ComplianceResultResponse> complianceResults;

    @Data
    @Builder
    public static class ScanInfo {
        private UUID id;
        private ScanStatus status;
        private ComplianceStatus overallStatus;
        private Double complianceScore;
        private Boolean needsManualReview;
        private String ocrRawText;
        private String imageUrl;
        private String errorMessage;
        private LocalDateTime createdAt;
        private LocalDateTime processedAt;
    }

    @Data
    @Builder
    public static class ProductInfo {
        private UUID id;
        private String name;
        private String category;
        private String brand;
    }
}
