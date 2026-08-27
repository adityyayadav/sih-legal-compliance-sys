package com.packsure.backend.scan.dto;

import lombok.Data;

import java.util.List;

/**
 * Standard JSON Contract that the Python FastAPI ML team must return.
 * If they change it, just update this DTO and the mapping in ScanService.
 */
@Data
public class MlScanResponse {
    
    private String overallStatus; // "COMPLIANT", "NON_COMPLIANT", or "PARTIAL"
    private List<MlDeclaration> declarations;
    private List<MlRuleResult> ruleResults;

    @Data
    public static class MlDeclaration {
        private String declarationType;
        private boolean isPresent;
        private String extractedValue;
        private Double confidenceScore;
        private String boundingBox;
    }

    @Data
    public static class MlRuleResult {
        private String ruleCode;
        private String ruleDescription;
        private String status; // "PASS", "FAIL", "WARNING"
        private String remarks;
    }
}
