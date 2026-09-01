package com.packsure.backend.scan.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * Response contract of the ML service's {@code POST /api/v1/analyze}
 * (see {@code ml-service/app/api/schemas.py} and {@code report_builder.py}).
 * Explicit {@code @JsonProperty} for each snake_case field so it maps regardless
 * of the active Jackson property-naming strategy.
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class MlAnalyzeResponse {

    @JsonProperty("product_id")
    private String productId;

    private String status;               // "SUCCESS"

    @JsonProperty("processed_at")
    private String processedAt;

    private Map<String, MlDeclaration> declarations;   // keyed by field name

    @JsonProperty("font_analysis")
    private List<MlFontAnalysis> fontAnalysis;

    private List<MlViolation> violations;

    @JsonProperty("overall_compliance_status")
    private String overallComplianceStatus;            // "COMPLIANT" | "NON COMPLIANT"

    @JsonProperty("confidence_flags")
    private MlConfidenceFlags confidenceFlags;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MlDeclaration {
        private boolean present;
        private String value;
        private Double confidence;
        private List<Integer> bbox;

        @JsonProperty("source_image_index")
        private Integer sourceImageIndex;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MlFontAnalysis {
        private String field;

        @JsonProperty("measured_height_mm")
        private Double measuredHeightMm;

        @JsonProperty("required_min_mm")
        private Double requiredMinMm;

        private Boolean compliant;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MlViolation {
        @JsonProperty("rule_ref")
        private String ruleRef;

        private String field;
        private String issue;
        private String severity;          // CRITICAL | MAJOR | MINOR
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MlConfidenceFlags {
        @JsonProperty("needs_manual_review")
        private boolean needsManualReview;

        @JsonProperty("low_confidence_fields")
        private List<String> lowConfidenceFields;
    }
}
