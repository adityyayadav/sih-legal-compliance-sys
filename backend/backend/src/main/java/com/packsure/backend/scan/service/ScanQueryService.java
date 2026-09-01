package com.packsure.backend.scan.service;

import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.exception.ResourceNotFoundException;
import com.packsure.backend.product.Product;
import com.packsure.backend.report.dto.ComplianceResultResponse;
import com.packsure.backend.report.dto.DeclarationResponse;
import com.packsure.backend.report.dto.DetailedScanResponse;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.scan.ScanSpecifications;
import com.packsure.backend.scan.dto.ScanSummaryResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ScanQueryService {

    private final ScanRepository scanRepository;

    /** Filter bag for {@link #listScans}. Any field may be null. */
    public record ScanFilter(ScanStatus status, UUID productId, LocalDate from, LocalDate to) {
    }

    /** ADMIN sees every scan; an INSPECTOR sees only their own. Optional filters are ANDed. */
    @Transactional(readOnly = true)
    public Page<ScanSummaryResponse> listScans(Pageable pageable, String requesterEmail,
                                               boolean admin, ScanFilter filter) {
        List<Specification<Scan>> specs = new ArrayList<>();
        if (!admin) {
            specs.add(ScanSpecifications.ownedBy(requesterEmail));
        }
        if (filter != null) {
            if (filter.status() != null) specs.add(ScanSpecifications.hasStatus(filter.status()));
            if (filter.productId() != null) specs.add(ScanSpecifications.hasProduct(filter.productId()));
            if (filter.from() != null) specs.add(ScanSpecifications.createdFrom(filter.from()));
            if (filter.to() != null) specs.add(ScanSpecifications.createdTo(filter.to()));
        }
        Specification<Scan> spec = specs.isEmpty() ? null : Specification.allOf(specs);
        return scanRepository.findAll(spec, pageable).map(this::toSummary);
    }

    @Transactional(readOnly = true)
    public DetailedScanResponse getDetailed(UUID scanId, String requesterEmail, boolean admin) {
        Scan scan = scanRepository.findDetailedById(scanId)
                .orElseThrow(() -> new ResourceNotFoundException("Scan not found"));
        assertVisible(scan, requesterEmail, admin);

        Product product = scan.getProduct();

        return DetailedScanResponse.builder()
                .scan(DetailedScanResponse.ScanInfo.builder()
                        .id(scan.getId())
                        .status(scan.getStatus())
                        .overallStatus(scan.getOverallStatus())
                        .complianceScore(scan.getComplianceScore())
                        .needsManualReview(scan.getNeedsManualReview())
                        .ocrRawText(scan.getOcrRawText())
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

    /** Shared owner check — throws 403 for an inspector looking at someone else's scan. */
    public static void assertVisible(Scan scan, String requesterEmail, boolean admin) {
        if (admin) return;
        if (scan.getScannedBy() == null || !scan.getScannedBy().getEmail().equals(requesterEmail)) {
            throw new AccessDeniedException("You do not have access to this scan");
        }
    }

    private ScanSummaryResponse toSummary(Scan scan) {
        Product product = scan.getProduct();
        return ScanSummaryResponse.builder()
                .id(scan.getId())
                .productName(product != null ? product.getName() : null)
                .status(scan.getStatus())
                .overallStatus(scan.getOverallStatus())
                .createdAt(scan.getCreatedAt())
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
