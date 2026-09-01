package com.packsure.backend.report.dto;

import com.packsure.backend.common.RuleStatus;
import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class ComplianceResultResponse {
    private UUID id;
    private String ruleCode;
    private String ruleDescription;
    private RuleStatus status;
    private String remarks;
}
