package com.packsure.backend.config;

import com.packsure.backend.common.ComplianceStatus;
import com.packsure.backend.common.Role;
import com.packsure.backend.common.RuleStatus;
import com.packsure.backend.common.ScanStatus;
import com.packsure.backend.product.Product;
import com.packsure.backend.product.ProductRepository;
import com.packsure.backend.scan.ComplianceResult;
import com.packsure.backend.scan.Declaration;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.user.User;
import com.packsure.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Seeds demo data on startup — {@code dev} profile only, and only when the DB is
 * empty. Gives the dashboard / detailed-view / PDF endpoints something to show.
 *
 * <pre>
 *   admin@packsure.test    / Admin@12345     (ADMIN)
 *   inspector@packsure.test / Inspector@123  (INSPECTOR)
 * </pre>
 */
@Slf4j
@Component
@Profile("dev")
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private static final String SAMPLE_IMAGE =
            "https://res.cloudinary.com/demo/image/upload/sample.jpg";

    private final UserRepository userRepository;
    private final ProductRepository productRepository;
    private final ScanRepository scanRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public void run(String... args) {
        if (userRepository.count() > 0) {
            return;
        }
        log.info("Seeding demo data (dev profile)...");

        User admin = userRepository.save(User.builder()
                .username("admin").email("admin@packsure.test")
                .password(passwordEncoder.encode("Admin@12345")).role(Role.ADMIN).build());
        User inspector = userRepository.save(User.builder()
                .username("inspector").email("inspector@packsure.test")
                .password(passwordEncoder.encode("Inspector@123")).role(Role.INSPECTOR).build());

        List<Product> products = productRepository.saveAll(List.of(
                product("Refined Sunflower Oil 1L", "EDIBLE_OIL", "SunGold", admin),
                product("Toor Dal 500g", "PULSES", "FarmFresh", admin),
                product("Instant Coffee 100g", "BEVERAGES", "MorningBrew", inspector),
                product("Whole Wheat Atta 5kg", "FLOUR", "GrainMill", inspector),
                product("Tomato Ketchup 950g", "SAUCES", "TangyTom", admin),
                product("Digestive Biscuits 250g", "SNACKS", "CrunchCo", inspector)));

        List<Scan> scans = new ArrayList<>();
        ComplianceStatus[] outcomes = {
                ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT,
                ComplianceStatus.PARTIAL, ComplianceStatus.NON_COMPLIANT,
                ComplianceStatus.COMPLIANT, ComplianceStatus.PARTIAL,
                ComplianceStatus.NON_COMPLIANT, ComplianceStatus.COMPLIANT
        };
        for (int i = 0; i < outcomes.length; i++) {
            Product p = products.get(i % products.size());
            User by = (i % 2 == 0) ? inspector : admin;
            scans.add(buildCompletedScan(p, by, outcomes[i], i));
        }
        // one that failed, one still processing
        scans.add(failedScan(products.get(0), inspector));
        scanRepository.saveAll(scans);

        log.info("Seeded {} users, {} products, {} scans",
                userRepository.count(), productRepository.count(), scanRepository.count());
    }

    private Product product(String name, String category, String brand, User by) {
        return Product.builder().name(name).category(category).brand(brand).createdBy(by).build();
    }

    private Scan buildCompletedScan(Product product, User by, ComplianceStatus outcome, int daysAgo) {
        Scan scan = Scan.builder()
                .imageUrl(SAMPLE_IMAGE)
                .status(ScanStatus.COMPLETED)
                .overallStatus(outcome)
                .product(product)
                .scannedBy(by)
                .processedAt(LocalDateTime.now().minusDays(daysAgo))
                .build();

        scan.getDeclarations().add(declaration(scan, "MANUFACTURER_NAME_ADDRESS", true, product.getBrand() + ", India", 0.94));
        scan.getDeclarations().add(declaration(scan, "NET_QUANTITY", true, "500 g", 0.88));
        scan.getDeclarations().add(declaration(scan, "MRP", outcome != ComplianceStatus.NON_COMPLIANT,
                outcome != ComplianceStatus.NON_COMPLIANT ? "Rs 120.00 (incl. of all taxes)" : null, 0.91));
        scan.getDeclarations().add(declaration(scan, "CONSUMER_CARE_DETAILS",
                outcome == ComplianceStatus.COMPLIANT, outcome == ComplianceStatus.COMPLIANT ? "care@brand.example" : null, 0.6));

        scan.getComplianceResults().add(rule(scan, "RULE_6_1_A_MANUFACTURER_NAME",
                "Name and address of manufacturer/packer", RuleStatus.PASS, "Declared"));
        scan.getComplianceResults().add(rule(scan, "RULE_6_7_NET_QUANTITY",
                "Net quantity in standard units",
                outcome == ComplianceStatus.COMPLIANT ? RuleStatus.PASS : RuleStatus.WARNING,
                outcome == ComplianceStatus.COMPLIANT ? "OK" : "Font height 3.8mm below required 4.0mm"));
        scan.getComplianceResults().add(rule(scan, "RULE_6_1_E_MRP", "Maximum Retail Price",
                outcome == ComplianceStatus.NON_COMPLIANT ? RuleStatus.FAIL : RuleStatus.PASS,
                outcome == ComplianceStatus.NON_COMPLIANT ? "MRP not found on label" : "Declared with tax clause"));
        scan.getComplianceResults().add(rule(scan, "RULE_6_1_F_CONSUMER_CARE",
                "Consumer care / complaint contact",
                outcome == ComplianceStatus.COMPLIANT ? RuleStatus.PASS : RuleStatus.FAIL,
                outcome == ComplianceStatus.COMPLIANT ? "Declared" : "Mandatory declaration missing"));
        return scan;
    }

    private Scan failedScan(Product product, User by) {
        return Scan.builder()
                .imageUrl(SAMPLE_IMAGE)
                .status(ScanStatus.FAILED)
                .product(product)
                .scannedBy(by)
                .errorMessage("ML processing failed: ML service unreachable")
                .processedAt(LocalDateTime.now().minusHours(2))
                .build();
    }

    private Declaration declaration(Scan scan, String type, boolean present, String value, double confidence) {
        return Declaration.builder()
                .scan(scan).declarationType(type).isPresent(present).extractedValue(value)
                .confidenceScore(present ? confidence : 0.0)
                .boundingBox(present ? "[" + rnd(50, 300) + "," + rnd(50, 500) + "," + rnd(100, 250) + "," + rnd(20, 60) + "]" : null)
                .build();
    }

    private ComplianceResult rule(Scan scan, String code, String description, RuleStatus status, String remarks) {
        return ComplianceResult.builder()
                .scan(scan).ruleCode(code).ruleDescription(description).status(status).remarks(remarks)
                .build();
    }

    private int rnd(int min, int max) {
        return ThreadLocalRandom.current().nextInt(min, max);
    }
}
