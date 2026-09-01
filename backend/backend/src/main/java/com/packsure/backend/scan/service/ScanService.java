package com.packsure.backend.scan.service;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.RuleStatus;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.exception.ResourceNotFoundException;
import com.packsure.backend.product.Product;
import com.packsure.backend.product.ProductRepository;
import com.packsure.backend.scan.ComplianceResult;
import com.packsure.backend.scan.Declaration;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.scan.dto.MlAnalyzeResponse;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlDeclaration;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlViolation;
import com.packsure.backend.scan.dto.ScanStatusResponse;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Orchestrates a scan: store image -> persist PENDING/PROCESSING -> call the ML
 * service ({@code POST /api/v1/analyze}) -> map the report onto our entities.
 * Deliberately NOT {@code @Transactional} at the class level: the slow image
 * upload and ML HTTP call must not hold a DB connection open.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ScanService {

    private static final int MAX_ERROR_MESSAGE_LENGTH = 1000;
    private static final Set<String> ALLOWED_IMAGE_TYPES = Set.of("image/jpeg", "image/png");

    private final ScanRepository scanRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;
    private final ImageStorageService imageStorage;
    private final MlAnalysisClient mlClient;

    public Scan processNewScan(MultipartFile imageFile, String productIdStr, String userEmail) {
        validateImage(imageFile);
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        UUID productId = parseUuid(productIdStr, "productId");
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found"));

        byte[] imageBytes;
        try {
            imageBytes = imageFile.getBytes();
        } catch (IOException e) {
            throw new IllegalArgumentException("Could not read the uploaded image");
        }

        // Slow work, outside any transaction.
        String imageUrl = imageStorage.uploadImage(imageFile);

        Scan scan = scanRepository.save(Scan.builder()
                .imageUrl(imageUrl)
                .status(ScanStatus.PENDING)
                .product(product)
                .scannedBy(user)
                .build());
        log.info("Scan {} created (product={}, by={})", scan.getId(), productId, userEmail);

        scan.setStatus(ScanStatus.PROCESSING);
        scan = scanRepository.save(scan);

        long start = System.currentTimeMillis();
        try {
            MlAnalyzeResponse report = mlClient.analyze(
                    imageBytes, imageFile.getOriginalFilename(), imageFile.getContentType(),
                    scan.getId().toString());
            applyReport(report, scan);
            scan.setStatus(ScanStatus.COMPLETED);
            scan.setProcessedAt(LocalDateTime.now());
            log.info("Scan {} COMPLETED in {} ms -> {}", scan.getId(),
                    System.currentTimeMillis() - start, scan.getOverallStatus());
        } catch (Exception e) {
            log.error("Scan {} FAILED after {} ms: {}", scan.getId(),
                    System.currentTimeMillis() - start, e.getMessage(), e);
            scan.setStatus(ScanStatus.FAILED);
            scan.setErrorMessage(truncate("ML processing failed: " + e.getMessage()));
            scan.setProcessedAt(LocalDateTime.now());
        }

        return scanRepository.save(scan);
    }

    @Transactional(readOnly = true)
    public ScanStatusResponse getScanStatus(UUID scanId, String requesterEmail, boolean admin) {
        Scan scan = scanRepository.findById(scanId)
                .orElseThrow(() -> new ResourceNotFoundException("Scan not found"));
        ScanQueryService.assertVisible(scan, requesterEmail, admin);
        return ScanStatusResponse.builder()
                .id(scan.getId())
                .status(scan.getStatus())
                .overallStatus(scan.getOverallStatus())
                .errorMessage(scan.getErrorMessage())
                .build();
    }

    private void validateImage(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Image file is required");
        }
        String contentType = file.getContentType();
        if (contentType == null || !ALLOWED_IMAGE_TYPES.contains(contentType.toLowerCase())) {
            throw new IllegalArgumentException("Unsupported image type: only JPEG and PNG are allowed");
        }
    }

    /** Maps the ML {@code /analyze} report onto the scan + its declarations + compliance results. */
    private void applyReport(MlAnalyzeResponse report, Scan scan) {
        List<MlViolation> violations = report.getViolations() == null ? List.of() : report.getViolations();
        Set<String> violatingFields = new HashSet<>();
        for (MlViolation v : violations) {
            if (v.getField() != null) violatingFields.add(v.getField());
        }

        // declarations (a map keyed by field name)
        if (report.getDeclarations() != null) {
            for (Map.Entry<String, MlDeclaration> e : report.getDeclarations().entrySet()) {
                MlDeclaration dec = e.getValue();
                scan.getDeclarations().add(Declaration.builder()
                        .scan(scan)
                        .declarationType(e.getKey().toUpperCase())
                        .isPresent(dec.isPresent())
                        .extractedValue(dec.getValue())
                        .confidenceScore(dec.getConfidence())
                        .boundingBox(dec.getBbox() == null ? null : dec.getBbox().toString())
                        .build());
            }
        }

        // one compliance result per violation
        for (MlViolation v : violations) {
            RuleStatus status = "MINOR".equalsIgnoreCase(v.getSeverity()) ? RuleStatus.WARNING : RuleStatus.FAIL;
            scan.getComplianceResults().add(ComplianceResult.builder()
                    .scan(scan)
                    .ruleCode(v.getRuleRef() != null && !v.getRuleRef().isBlank() ? v.getRuleRef() : v.getField())
                    .ruleDescription(v.getIssue())
                    .status(status)
                    .remarks("Field: " + v.getField() + " | Severity: " + v.getSeverity())
                    .build());
        }

        // a PASS row for every present declaration that has no violation
        if (report.getDeclarations() != null) {
            report.getDeclarations().forEach((field, dec) -> {
                if (dec.isPresent() && !violatingFields.contains(field)) {
                    scan.getComplianceResults().add(ComplianceResult.builder()
                            .scan(scan)
                            .ruleCode(field.toUpperCase())
                            .ruleDescription("Declaration present and conforming")
                            .status(RuleStatus.PASS)
                            .remarks(dec.getValue())
                            .build());
                }
            });
        }

        scan.setOverallStatus(deriveOverall(report.getOverallComplianceStatus(), violations));

        if (report.getConfidenceFlags() != null) {
            scan.setNeedsManualReview(report.getConfidenceFlags().isNeedsManualReview());
        }
    }

    /** ML returns COMPLIANT / "NON COMPLIANT"; we add PARTIAL when only MINOR issues exist. */
    private ComplianceStatus deriveOverall(String mlStatus, List<MlViolation> violations) {
        String normalized = mlStatus == null ? "" : mlStatus.trim().toUpperCase().replace(" ", "_");
        if ("COMPLIANT".equals(normalized)) return ComplianceStatus.COMPLIANT;
        boolean anySevere = violations.stream()
                .anyMatch(v -> "CRITICAL".equalsIgnoreCase(v.getSeverity())
                        || "MAJOR".equalsIgnoreCase(v.getSeverity()));
        if (!violations.isEmpty() && !anySevere) return ComplianceStatus.PARTIAL;
        return ComplianceStatus.NON_COMPLIANT;
    }

    private UUID parseUuid(String value, String field) {
        try {
            return UUID.fromString(value);
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new IllegalArgumentException(field + " is not a valid UUID");
        }
    }

    private String truncate(String s) {
        if (s == null) return null;
        return s.length() <= MAX_ERROR_MESSAGE_LENGTH ? s : s.substring(0, MAX_ERROR_MESSAGE_LENGTH);
    }
}
