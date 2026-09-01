package com.packsure.backend.dashboard.service;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.RuleStatus;
import com.packsure.backend.dashboard.dto.DashboardStatsResponse;
import com.packsure.backend.scan.ComplianceResultRepository;
import com.packsure.backend.scan.ComplianceResultRepository.RuleCodeCount;
import com.packsure.backend.scan.ScanRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Aggregate stats for the dashboard. ADMIN gets project-wide numbers; an
 * INSPECTOR gets numbers for their own scans only.
 */
@Service
@RequiredArgsConstructor
public class DashboardService {

    private static final int TOP_VIOLATIONS_LIMIT = 5;

    private final ScanRepository scanRepository;
    private final ComplianceResultRepository complianceResultRepository;

    @Transactional(readOnly = true)
    public DashboardStatsResponse getStats(String requesterEmail, boolean admin) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime sevenDaysAgo = now.minusDays(7);
        LocalDateTime thirtyDaysAgo = now.minusDays(30);
        PageRequest topN = PageRequest.of(0, TOP_VIOLATIONS_LIMIT);

        long total;
        long compliant;
        long nonCompliant;
        long partial;
        long last7;
        long last30;
        List<RuleCodeCount> violations;

        if (admin) {
            total = scanRepository.count();
            compliant = scanRepository.countByOverallStatus(ComplianceStatus.COMPLIANT);
            nonCompliant = scanRepository.countByOverallStatus(ComplianceStatus.NON_COMPLIANT);
            partial = scanRepository.countByOverallStatus(ComplianceStatus.PARTIAL);
            last7 = scanRepository.countByCreatedAtAfter(sevenDaysAgo);
            last30 = scanRepository.countByCreatedAtAfter(thirtyDaysAgo);
            violations = complianceResultRepository.findTopViolations(RuleStatus.FAIL, topN);
        } else {
            total = scanRepository.countByScannedByEmail(requesterEmail);
            compliant = scanRepository.countByOverallStatusAndScannedByEmail(ComplianceStatus.COMPLIANT, requesterEmail);
            nonCompliant = scanRepository.countByOverallStatusAndScannedByEmail(ComplianceStatus.NON_COMPLIANT, requesterEmail);
            partial = scanRepository.countByOverallStatusAndScannedByEmail(ComplianceStatus.PARTIAL, requesterEmail);
            last7 = scanRepository.countByCreatedAtAfterAndScannedByEmail(sevenDaysAgo, requesterEmail);
            last30 = scanRepository.countByCreatedAtAfterAndScannedByEmail(thirtyDaysAgo, requesterEmail);
            violations = complianceResultRepository.findTopViolationsByOwner(RuleStatus.FAIL, requesterEmail, topN);
        }

        return DashboardStatsResponse.builder()
                .totalScans(total)
                .compliant(compliant)
                .nonCompliant(nonCompliant)
                .partial(partial)
                .scansLast7Days(last7)
                .scansLast30Days(last30)
                .topViolations(violations.stream()
                        .map(row -> DashboardStatsResponse.TopViolation.builder()
                                .ruleCode(row.getRuleCode())
                                .count(row.getCount())
                                .build())
                        .toList())
                .build();
    }
}
