package com.packsure.backend.scan.service;

import com.packsure.backend.exception.ResourceNotFoundException;
import com.packsure.backend.product.Product;
import com.packsure.backend.report.dto.ComplianceResultResponse;
import com.packsure.backend.report.dto.DeclarationResponse;
import com.packsure.backend.report.dto.DetailedScanResponse;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.scan.dto.ScanSummaryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ScanQueryService {

    private final ScanRepository scanRepository;

    @Transactional(readOnly = true)
    public Page<ScanSummaryResponse> listScans(Pageable pageable) {
        return scanRepository.findAll(pageable).map(scan -> {
            Product product = scan.getProduct();
            return ScanSummaryResponse.builder()
                    .id(scan.getId())
                    .productName(product != null ? product.getName() : null)
                    .status(scan.getStatus())
                    .overallStatus(scan.getOverallStatus())
                    .createdAt(scan.getCreatedAt())
                    .build();
        });
    }

    @Transactional(readOnly = true)
    public DetailedScanResponse getDetailed(UUID scanId) {
        Scan scan = scanRepository.findDetailedById(scanId)
                .orElseThrow(() -> new ResourceNotFoundException("Scan not found"));

        Product product = scan.getProduct();

        return DetailedScanResponse.builder()
                .scan(DetailedScanResponse.ScanInfo.builder()
                        .id(scan.getId())
                        .status(scan.getStatus())
                        .overallStatus(scan.getOverallStatus())
                        .imageUrl(scan.getImageUrl())
                        .errorMessage(scan.getErrorMessage())
                        .createdAt(scan.getCreatedAt())
                        .processedAt(scan.getProcessedAt())
                        .build())
                .product(product == null ? null : DetailedScanResponse.ProductInfo.builder()
                        .id(product.getId())
                        .name(product.getName())
                        .category(product.getCategory())
                        .brand(product.getBrand())
                        .build())
                .declarations(mapDeclarations(scan))
                .complianceResults(mapComplianceResults(scan))
                .build();
    }

    private List<DeclarationResponse> mapDeclarations(Scan scan) {
        return scan.getDeclarations().stream()
                .map(d -> DeclarationResponse.builder()
                        .id(d.getId())
                        .declarationType(d.getDeclarationType())
                        .present(d.isPresent())
                        .extractedValue(d.getExtractedValue())
                        .confidenceScore(d.getConfidenceScore())
                        .boundingBox(d.getBoundingBox())
                        .build())
                .toList();
    }

    private List<ComplianceResultResponse> mapComplianceResults(Scan scan) {
        return scan.getComplianceResults().stream()
                .map(cr -> ComplianceResultResponse.builder()
                        .id(cr.getId())
                        .ruleCode(cr.getRuleCode())
                        .ruleDescription(cr.getRuleDescription())
                        .status(cr.getStatus())
                        .remarks(cr.getRemarks())
                        .build())
                .toList();
    }
}
