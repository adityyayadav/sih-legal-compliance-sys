package com.packsure.backend.report.dto;

import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class DeclarationResponse {
    private UUID id;
    private String declarationType;
    private boolean present;
    private String extractedValue;
    private Double confidenceScore;
    private String boundingBox;
}
