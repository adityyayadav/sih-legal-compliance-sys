package com.packsure.backend.dashboard.controller;

import com.packsure.backend.auth.SecurityUtils;
import com.packsure.backend.dashboard.dto.DashboardStatsResponse;
import com.packsure.backend.dashboard.service.DashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final DashboardService dashboardService;

    @GetMapping("/stats")
    public ResponseEntity<DashboardStatsResponse> stats(@AuthenticationPrincipal UserDetails principal) {
        return ResponseEntity.ok(dashboardService.getStats(
                principal.getUsername(), SecurityUtils.isAdmin(principal)));
    }
}
