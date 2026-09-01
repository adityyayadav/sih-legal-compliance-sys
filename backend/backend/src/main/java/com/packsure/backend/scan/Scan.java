package com.packsure.backend.scan;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.product.Product;
import com.packsure.backend.user.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "scans")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Scan {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private String imageUrl;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ScanStatus status;

    @Enumerated(EnumType.STRING)
    private ComplianceStatus overallStatus;

    /** 0..1 aggregate score from the ML service, if provided. */
    private Double complianceScore;

    /** Raw OCR text from the ML service, kept for audit / debugging. */
    @Column(columnDefinition = "TEXT")
    private String ocrRawText;

    @Column(columnDefinition = "TEXT")
    private String errorMessage;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id")
    private Product product;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scanned_by_id", nullable = false)
    private User scannedBy;

    @OneToMany(mappedBy = "scan", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Declaration> declarations = new ArrayList<>();

    @OneToMany(mappedBy = "scan", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<ComplianceResult> complianceResults = new ArrayList<>();

    @CreationTimestamp
    @Column(updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime processedAt;
}
