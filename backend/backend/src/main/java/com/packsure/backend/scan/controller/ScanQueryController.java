package com.packsure.backend.scan.controller;

import com.packsure.backend.report.dto.DetailedScanResponse;
import com.packsure.backend.scan.dto.ScanSummaryResponse;
import com.packsure.backend.scan.service.ScanQueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanQueryController {

    private final ScanQueryService scanQueryService;

    /** Paginated list of scans for the dashboard. {@code ?page=0&size=20&sort=createdAt,desc} */
    @GetMapping
    public ResponseEntity<Page<ScanSummaryResponse>> list(
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable) {
        return ResponseEntity.ok(scanQueryService.listScans(pageable));
    }

    /** Full nested view of a scan for the results page. */
    @GetMapping("/{id}/detailed")
    public ResponseEntity<DetailedScanResponse> detailed(@PathVariable UUID id) {
        return ResponseEntity.ok(scanQueryService.getDetailed(id));
    }
}
