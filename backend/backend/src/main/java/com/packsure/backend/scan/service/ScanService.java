package com.packsure.backend.scan.service;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.RuleStatus;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.product.Product;
import com.packsure.backend.product.ProductRepository;
import com.packsure.backend.scan.ComplianceResult;
import com.packsure.backend.scan.Declaration;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.scan.dto.MlScanResponse;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class ScanService {

    private final ScanRepository scanRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;
    private final CloudinaryService cloudinaryService;
    private final MlServiceClient mlServiceClient;

    @Transactional
    public Scan processNewScan(MultipartFile imageFile, String productIdStr, String userEmail) {
        
        // 1. Fetch relations
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));
        Product product = productRepository.findById(java.util.UUID.fromString(productIdStr))
                .orElseThrow(() -> new IllegalArgumentException("Product not found"));

        // 2. Upload Image to Cloudinary
        String imageUrl = cloudinaryService.uploadImage(imageFile);

        // 3. Create initial PENDING Scan
        Scan scan = Scan.builder()
                .imageUrl(imageUrl)
                .status(ScanStatus.PROCESSING)
                .product(product)
                .scannedBy(user)
                .build();
        scan = scanRepository.save(scan);

        try {
            // 4. Send Image URL to Python ML Service
            MlScanResponse mlResponse = mlServiceClient.analyzeImageViaMl(imageUrl);

            // 5. Map ML JSON Response into our SQL Tables
            mapMlResponseToScan(mlResponse, scan);

            // 6. Finalize Scan Status
            scan.setStatus(ScanStatus.COMPLETED);
            scan.setProcessedAt(LocalDateTime.now());
            
        } catch (Exception e) {
            scan.setStatus(ScanStatus.FAILED);
            scan.setErrorMessage("ML Process failed: " + e.getMessage());
            scan.setProcessedAt(LocalDateTime.now());
        }

        return scanRepository.save(scan);
    }

    private void mapMlResponseToScan(MlScanResponse mlResponse, Scan scan) {
        // Overall status
        scan.setOverallStatus(ComplianceStatus.valueOf(mlResponse.getOverallStatus()));

        // Map Extracted Declarations
        if (mlResponse.getDeclarations() != null) {
            mlResponse.getDeclarations().forEach(mlDec -> {
                Declaration dec = Declaration.builder()
                        .scan(scan)
                        .declarationType(mlDec.getDeclarationType())
                        .isPresent(mlDec.isPresent())
                        .extractedValue(mlDec.getExtractedValue())
                        .confidenceScore(mlDec.getConfidenceScore())
                        .boundingBox(mlDec.getBoundingBox())
                        .build();
                scan.getDeclarations().add(dec);
            });
        }

        // Map Rule Compliance Results
        if (mlResponse.getRuleResults() != null) {
            mlResponse.getRuleResults().forEach(mlRule -> {
                ComplianceResult cr = ComplianceResult.builder()
                        .scan(scan)
                        .ruleCode(mlRule.getRuleCode())
                        .ruleDescription(mlRule.getRuleDescription())
                        .status(RuleStatus.valueOf(mlRule.getStatus()))
                        .remarks(mlRule.getRemarks())
                        .build();
                scan.getComplianceResults().add(cr);
            });
        }
    }
}
