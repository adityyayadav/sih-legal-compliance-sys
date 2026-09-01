package com.packsure.backend.scan.controller;

import com.packsure.backend.auth.SecurityUtils;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.report.dto.DetailedScanResponse;
import com.packsure.backend.scan.dto.ScanSummaryResponse;
import com.packsure.backend.scan.service.ScanQueryService;
import com.packsure.backend.scan.service.ScanQueryService.ScanFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.UUID;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanQueryController {

    private final ScanQueryService scanQueryService;

    /**
     * Paginated list. ADMIN sees all scans; an INSPECTOR sees only their own.
     * Optional filters: {@code ?status=COMPLETED&productId=<uuid>&from=2026-08-01&to=2026-08-31}.
     */
    @GetMapping
    public ResponseEntity<Page<ScanSummaryResponse>> list(
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable,
            @RequestParam(required = false) ScanStatus status,
            @RequestParam(required = false) UUID productId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
            @AuthenticationPrincipal UserDetails principal) {
        return ResponseEntity.ok(scanQueryService.listScans(
                pageable, principal.getUsername(), SecurityUtils.isAdmin(principal),
                new ScanFilter(status, productId, from, to)));
    }

    /** Full nested view. An INSPECTOR may only open their own scans. */
    @GetMapping("/{id}/detailed")
    public ResponseEntity<DetailedScanResponse> detailed(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserDetails principal) {
        return ResponseEntity.ok(scanQueryService.getDetailed(
                id, principal.getUsername(), SecurityUtils.isAdmin(principal)));
    }
}
