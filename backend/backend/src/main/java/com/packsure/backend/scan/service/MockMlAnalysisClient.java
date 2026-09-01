package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlScanResponse;
import com.packsure.backend.scan.dto.MlScanResponse.MlDeclaration;
import com.packsure.backend.scan.dto.MlScanResponse.MlRuleResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Dev/test stand-in for the ML service. Produces a deterministic, realistic
 * {@link MlScanResponse} based on the image URL so the scan pipeline can be
 * demoed end to end without a running model service.
 */
@Slf4j
@Service
@Profile("dev | test")
public class MockMlAnalysisClient implements MlAnalysisClient {

    @Override
    public MlScanResponse analyzeImageViaMl(String imageUrl) {
        int bucket = Math.floorMod((imageUrl == null ? "" : imageUrl).hashCode(), 3);
        log.info("[dev] MockMlAnalysisClient producing bucket-{} result for {}", bucket, imageUrl);

        return switch (bucket) {
            case 0 -> compliant();
            case 1 -> partial();
            default -> nonCompliant();
        };
    }

    private MlScanResponse compliant() {
        MlScanResponse r = new MlScanResponse();
        r.setOverallStatus("COMPLIANT");
        r.setDeclarations(List.of(
                decl("MANUFACTURER_NAME_ADDRESS", true, "ABC Foods Pvt Ltd, Pune, MH 411001", 0.95),
                decl("COMMODITY_NAME", true, "Refined Sunflower Oil", 0.93),
                decl("NET_QUANTITY", true, "1 L", 0.91),
                decl("MRP", true, "MRP Rs 185.00 (incl. of all taxes)", 0.94),
                decl("MFG_DATE", true, "07/2026", 0.88),
                decl("CONSUMER_CARE_DETAILS", true, "care@abcfoods.example / 1800-000-000", 0.86),
                decl("COUNTRY_OF_ORIGIN", true, "India", 0.9)));
        r.setRuleResults(List.of(
                rule("RULE_6_1_A_MANUFACTURER_NAME", "Name & address of manufacturer/packer", "PASS", "Declared"),
                rule("RULE_6_1_B_COMMODITY_NAME", "Common/generic name of commodity", "PASS", "Declared"),
                rule("RULE_6_7_NET_QUANTITY", "Net quantity in standard units", "PASS", "1 L, cap-height 4.3 mm (>= 4.0 mm)"),
                rule("RULE_6_1_E_MRP", "Maximum Retail Price", "PASS", "Declared with 'incl. of all taxes'"),
                rule("RULE_6_1_D_MFG_DATE", "Month & year of manufacture", "PASS", "07/2026"),
                rule("RULE_6_1_F_CONSUMER_CARE", "Consumer care / complaint contact", "PASS", "Email and phone present")));
        return r;
    }

    private MlScanResponse partial() {
        MlScanResponse r = new MlScanResponse();
        r.setOverallStatus("PARTIAL");
        r.setDeclarations(List.of(
                decl("MANUFACTURER_NAME_ADDRESS", true, "GrainMill Industries, Indore, MP", 0.9),
                decl("COMMODITY_NAME", true, "Whole Wheat Atta", 0.92),
                decl("NET_QUANTITY", true, "5 kg", 0.87),
                decl("MRP", true, "MRP Rs 260.00", 0.8),
                decl("MFG_DATE", true, "05/2026", 0.83),
                decl("CONSUMER_CARE_DETAILS", false, null, 0.0)));
        r.setRuleResults(List.of(
                rule("RULE_6_1_A_MANUFACTURER_NAME", "Name & address of manufacturer/packer", "PASS", "Declared"),
                rule("RULE_6_1_B_COMMODITY_NAME", "Common/generic name of commodity", "PASS", "Declared"),
                rule("RULE_6_7_NET_QUANTITY", "Net quantity in standard units", "WARNING", "Cap-height 3.7 mm is below the required 4.0 mm"),
                rule("RULE_6_1_E_MRP", "Maximum Retail Price", "WARNING", "'inclusive of all taxes' clause not detected"),
                rule("RULE_6_1_D_MFG_DATE", "Month & year of manufacture", "PASS", "05/2026"),
                rule("RULE_6_1_F_CONSUMER_CARE", "Consumer care / complaint contact", "FAIL", "Mandatory declaration missing")));
        return r;
    }

    private MlScanResponse nonCompliant() {
        MlScanResponse r = new MlScanResponse();
        r.setOverallStatus("NON_COMPLIANT");
        r.setDeclarations(List.of(
                decl("MANUFACTURER_NAME_ADDRESS", true, "TangyTom", 0.72),
                decl("COMMODITY_NAME", true, "Tomato Ketchup", 0.9),
                decl("NET_QUANTITY", true, "950 g", 0.85),
                decl("MRP", false, null, 0.0),
                decl("MFG_DATE", false, null, 0.0),
                decl("CONSUMER_CARE_DETAILS", false, null, 0.0)));
        r.setRuleResults(List.of(
                rule("RULE_6_1_A_MANUFACTURER_NAME", "Name & address of manufacturer/packer", "FAIL", "Address not declared (name only)"),
                rule("RULE_6_1_B_COMMODITY_NAME", "Common/generic name of commodity", "PASS", "Declared"),
                rule("RULE_6_7_NET_QUANTITY", "Net quantity in standard units", "PASS", "950 g"),
                rule("RULE_6_1_E_MRP", "Maximum Retail Price", "FAIL", "MRP not found on label"),
                rule("RULE_6_1_D_MFG_DATE", "Month & year of manufacture", "FAIL", "Manufacture date not found"),
                rule("RULE_6_1_F_CONSUMER_CARE", "Consumer care / complaint contact", "FAIL", "Mandatory declaration missing")));
        return r;
    }

    private MlDeclaration decl(String type, boolean present, String value, double confidence) {
        MlDeclaration d = new MlDeclaration();
        d.setDeclarationType(type);
        d.setPresent(present);
        d.setExtractedValue(value);
        d.setConfidenceScore(present ? confidence : 0.0);
        d.setBoundingBox(present ? "[" + rand(40, 300) + "," + rand(40, 520) + "," + rand(90, 260) + "," + rand(22, 56) + "]" : null);
        return d;
    }

    private MlRuleResult rule(String code, String description, String status, String remarks) {
        MlRuleResult m = new MlRuleResult();
        m.setRuleCode(code);
        m.setRuleDescription(description);
        m.setStatus(status);
        m.setRemarks(remarks);
        return m;
    }

    private int rand(int min, int max) {
        return min + (int) (Math.random() * (max - min));
    }
}
