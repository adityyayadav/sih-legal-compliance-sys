package com.packsure.backend;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.product.Product;
import com.packsure.backend.product.ProductRepository;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.support.AbstractIntegrationTest;
import com.packsure.backend.user.User;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class ScanAccessControlTest extends AbstractIntegrationTest {

    @Autowired
    ScanRepository scans;
    @Autowired
    ProductRepository products;

    @Test
    void inspector_sees_only_own_scans_admin_sees_all() throws Exception {
        String inspAToken = registerInspector("insA", "insA@test.com", "secret123");
        String inspBToken = registerInspector("insB", "insB@test.com", "secret123");
        String adminToken = createAdmin("root@test.com", "Admin@12345");

        User inspA = users.findByEmail("insA@test.com").orElseThrow();
        User inspB = users.findByEmail("insB@test.com").orElseThrow();
        Product p = products.save(Product.builder()
                .name("Oil").category("EDIBLE_OIL").createdBy(inspA).build());

        seedScan(inspA, p, ComplianceStatus.COMPLIANT);
        seedScan(inspA, p, ComplianceStatus.NON_COMPLIANT);
        Scan bScan = seedScan(inspB, p, ComplianceStatus.PARTIAL);

        mvc.perform(get("/api/scans").header("Authorization", bearer(inspAToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(2));

        mvc.perform(get("/api/scans").header("Authorization", bearer(inspBToken)))
                .andExpect(jsonPath("$.totalElements").value(1));

        mvc.perform(get("/api/scans").header("Authorization", bearer(adminToken)))
                .andExpect(jsonPath("$.totalElements").value(3));

        // A cannot open B's scan
        mvc.perform(get("/api/scans/" + bScan.getId() + "/detailed")
                        .header("Authorization", bearer(inspAToken)))
                .andExpect(status().isForbidden());

        // admin can
        mvc.perform(get("/api/scans/" + bScan.getId() + "/detailed")
                        .header("Authorization", bearer(adminToken)))
                .andExpect(status().isOk());
    }

    @Test
    void list_filters_by_status() throws Exception {
        String token = registerInspector("filt", "filt@test.com", "secret123");
        User u = users.findByEmail("filt@test.com").orElseThrow();
        Product p = products.save(Product.builder().name("P").category("C").createdBy(u).build());
        seedScanWithStatus(u, p, ScanStatus.COMPLETED);
        seedScanWithStatus(u, p, ScanStatus.FAILED);

        mvc.perform(get("/api/scans").param("status", "FAILED")
                        .header("Authorization", bearer(token)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.content[0].status").value("FAILED"));
    }

    @Test
    void dashboard_stats_are_scoped_per_inspector() throws Exception {
        String token = registerInspector("dash", "dash@test.com", "secret123");
        String otherToken = registerInspector("dash2", "dash2@test.com", "secret123");
        User u = users.findByEmail("dash@test.com").orElseThrow();
        Product p = products.save(Product.builder().name("P").category("C").createdBy(u).build());
        seedScan(u, p, ComplianceStatus.COMPLIANT);
        seedScan(u, p, ComplianceStatus.COMPLIANT);

        mvc.perform(get("/api/dashboard/stats").header("Authorization", bearer(token)))
                .andExpect(jsonPath("$.totalScans").value(2))
                .andExpect(jsonPath("$.compliant").value(2));

        mvc.perform(get("/api/dashboard/stats").header("Authorization", bearer(otherToken)))
                .andExpect(jsonPath("$.totalScans").value(0));
    }

    private Scan seedScan(User by, Product product, ComplianceStatus outcome) {
        return scans.save(Scan.builder()
                .imageUrl("https://example.test/img.jpg")
                .status(ScanStatus.COMPLETED)
                .overallStatus(outcome)
                .product(product)
                .scannedBy(by)
                .build());
    }

    private Scan seedScanWithStatus(User by, Product product, ScanStatus status) {
        return scans.save(Scan.builder()
                .imageUrl("https://example.test/img.jpg")
                .status(status)
                .product(product)
                .scannedBy(by)
                .build());
    }
}
