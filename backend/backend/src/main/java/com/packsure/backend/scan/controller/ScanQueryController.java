package com.packsure.backend.scan.controller;

import com.packsure.backend.auth.SecurityUtils;
import com.packsure.backend.report.dto.DetailedScanResponse;
import com.packsure.backend.scan.dto.ScanSummaryResponse;
import com.packsure.backend.scan.service.ScanQueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
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

    /** Paginated list. ADMIN sees all scans; an INSPECTOR sees only their own. */
    @GetMapping
    public ResponseEntity<Page<ScanSummaryResponse>> list(
            @PageableDefault(size = 20, sort = "createdAt") Pageable pageable,
            @AuthenticationPrincipal UserDetails principal) {
        return ResponseEntity.ok(scanQueryService.listScans(
                pageable, principal.getUsername(), SecurityUtils.isAdmin(principal)));
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
