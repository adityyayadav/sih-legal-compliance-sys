package com.packsure.backend.scan;

import com.packsure.backend.common.RuleStatus;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "compliance_results")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ComplianceResult {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scan_id", nullable = false)
    private Scan scan;

    @Column(nullable = false)
    private String ruleCode;

    @Column(columnDefinition = "TEXT")
    private String ruleDescription;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private RuleStatus status;

    @Column(columnDefinition = "TEXT")
    private String remarks;
}
