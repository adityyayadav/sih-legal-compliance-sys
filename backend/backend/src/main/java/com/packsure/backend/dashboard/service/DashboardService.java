package com.packsure.backend.dashboard.service;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.RuleStatus;
import com.packsure.backend.dashboard.dto.DashboardStatsResponse;
import com.packsure.backend.scan.ComplianceResultRepository;
import com.packsure.backend.scan.ScanRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class DashboardService {

    private static final int TOP_VIOLATIONS_LIMIT = 5;

    private final ScanRepository scanRepository;
    private final ComplianceResultRepository complianceResultRepository;

    @Transactional(readOnly = true)
    public DashboardStatsResponse getStats() {
        LocalDateTime now = LocalDateTime.now();

        List<DashboardStatsResponse.TopViolation> topViolations = complianceResultRepository
                .findTopViolations(RuleStatus.FAIL, PageRequest.of(0, TOP_VIOLATIONS_LIMIT))
                .stream()
                .map(row -> DashboardStatsResponse.TopViolation.builder()
                        .ruleCode(row.getRuleCode())
                        .count(row.getCount())
                        .build())
                .toList();

        return DashboardStatsResponse.builder()
                .totalScans(scanRepository.count())
                .compliant(scanRepository.countByOverallStatus(ComplianceStatus.COMPLIANT))
                .nonCompliant(scanRepository.countByOverallStatus(ComplianceStatus.NON_COMPLIANT))
                .partial(scanRepository.countByOverallStatus(ComplianceStatus.PARTIAL))
                .scansLast7Days(scanRepository.countByCreatedAtAfter(now.minusDays(7)))
                .scansLast30Days(scanRepository.countByCreatedAtAfter(now.minusDays(30)))
                .topViolations(topViolations)
                .build();
    }
}
