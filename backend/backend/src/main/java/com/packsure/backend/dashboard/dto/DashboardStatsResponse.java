package com.packsure.backend.dashboard.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class DashboardStatsResponse {

    private long totalScans;

    private long compliant;
    private long nonCompliant;
    private long partial;

    private long scansLast7Days;
    private long scansLast30Days;

    private List<TopViolation> topViolations;

    @Data
    @Builder
    public static class TopViolation {
        private String ruleCode;
        private long count;
    }
}
