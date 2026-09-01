package com.packsure.backend.scan.controller;

import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.dto.ScanStatusResponse;
import com.packsure.backend.scan.service.ScanService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanController {

    private final ScanService scanService;

    /**
     * Submit a product-label image for compliance analysis.
     * multipart/form-data: {@code file} (image) + {@code productId}.
     * Processing is synchronous for the PoC; the response carries the final state.
     */
    @PostMapping
    public ResponseEntity<ScanStatusResponse> submitScan(
            @RequestParam("file") MultipartFile file,
            @RequestParam("productId") String productId,
            @AuthenticationPrincipal UserDetails principal) {

        Scan scan = scanService.processNewScan(file, productId, principal.getUsername());

        return ResponseEntity.status(HttpStatus.CREATED).body(ScanStatusResponse.builder()
                .id(scan.getId())
                .status(scan.getStatus())
                .overallStatus(scan.getOverallStatus())
                .errorMessage(scan.getErrorMessage())
                .build());
    }

    /** Polling endpoint for the frontend while a scan is processing. */
    @GetMapping("/{id}/status")
    public ResponseEntity<ScanStatusResponse> getStatus(@PathVariable UUID id) {
        return ResponseEntity.ok(scanService.getScanStatus(id));
    }
}
