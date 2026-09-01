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
import com.packsure.backend.scan.dto.MlScanResponse;
import com.packsure.backend.scan.dto.ScanStatusResponse;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.Set;
import java.util.UUID;

/**
 * Orchestrates a scan: Cloudinary upload -> persist PENDING -> call the ML
 * service -> persist the result. Deliberately NOT {@code @Transactional} at the
 * class level: the slow Cloudinary upload and ML HTTP call must not hold a DB
 * connection open. Each {@code scanRepository.save(...)} is its own short
 * transaction; the final save cascades the declarations / compliance results.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ScanService {

    /** Postgres/H2 column is TEXT, but keep error messages sane. */
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
            MlScanResponse mlResponse = mlClient.analyzeImageViaMl(imageUrl);
            applyMlResponse(mlResponse, scan);
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

    private void applyMlResponse(MlScanResponse mlResponse, Scan scan) {
        scan.setOverallStatus(parseComplianceStatus(mlResponse.getOverallStatus()));

        if (mlResponse.getDeclarations() != null) {
            mlResponse.getDeclarations().forEach(mlDec -> scan.getDeclarations().add(
                    Declaration.builder()
                            .scan(scan)
                            .declarationType(mlDec.getDeclarationType())
                            .isPresent(mlDec.isPresent())
                            .extractedValue(mlDec.getExtractedValue())
                            .confidenceScore(mlDec.getConfidenceScore())
                            .boundingBox(mlDec.getBoundingBox())
                            .build()));
        }

        if (mlResponse.getRuleResults() != null) {
            mlResponse.getRuleResults().forEach(mlRule -> scan.getComplianceResults().add(
                    ComplianceResult.builder()
                            .scan(scan)
                            .ruleCode(mlRule.getRuleCode())
                            .ruleDescription(mlRule.getRuleDescription())
                            .status(parseRuleStatus(mlRule.getStatus()))
                            .remarks(mlRule.getRemarks())
                            .build()));
        }
    }

    private ComplianceStatus parseComplianceStatus(String value) {
        if (value == null || value.isBlank()) return null;
        try {
            return ComplianceStatus.valueOf(value.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            log.warn("Unrecognized overall compliance status from ML: '{}'", value);
            return null;
        }
    }

    private RuleStatus parseRuleStatus(String value) {
        if (value == null || value.isBlank()) return RuleStatus.NOT_APPLICABLE;
        try {
            return RuleStatus.valueOf(value.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            log.warn("Unrecognized rule status from ML: '{}'", value);
            return RuleStatus.NOT_APPLICABLE;
        }
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
