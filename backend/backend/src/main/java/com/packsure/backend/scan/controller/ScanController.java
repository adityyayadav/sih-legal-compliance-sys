package com.packsure.backend.scan.controller;

import com.packsure.backend.scan.service.ScanService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/scans")
@RequiredArgsConstructor
public class ScanController {

    private final ScanService scanService;

    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyzeProduct(
            @RequestParam("image") MultipartFile image,
            @RequestParam("productId") String productId) {

        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String userEmail = ((UserDetails) authentication.getPrincipal()).getUsername();

        // Warning: This blocks until ML returns (Synchronous). 
        // Fine for short ML queues, but consider WebSocket/Async for production.
        var completedScan = scanService.processNewScan(image, productId, userEmail);

        Map<String, Object> response = new HashMap<>();
        response.put("scanId", completedScan.getId());
        response.put("status", completedScan.getStatus());
        response.put("complianceStatus", completedScan.getOverallStatus());
        response.put("message", "Scan processed successfully.");

        return new ResponseEntity<>(response, HttpStatus.OK);
    }
}
