package com.packsure.backend.scan.service;

import com.packsure.backend.scan.dto.MlAnalyzeResponse;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlConfidenceFlags;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlDeclaration;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlFontAnalysis;
import com.packsure.backend.scan.dto.MlAnalyzeResponse.MlViolation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Dev/test stand-in for the ML service. Produces a deterministic
 * {@link MlAnalyzeResponse} — same JSON contract as the real
 * {@code POST /api/v1/analyze} — so the scan pipeline can be demoed end to end
 * without a running model service.
 */
@Slf4j
@Service
@ConditionalOnProperty(prefix = "app.ml", name = "mock", havingValue = "true")
public class MockMlAnalysisClient implements MlAnalysisClient {

    private static final String MANUFACTURER = "manufacturer_or_packer_or_importer_name_address";
    private static final String COMMODITY = "common_or_generic_name";
    private static final String NET_QTY = "net_quantity";
    private static final String MRP = "mrp";
    private static final String MFG_DATE = "mfg_or_pack_or_import_date";
    private static final String CONSUMER_CARE = "consumer_care_details";
    private static final String COUNTRY = "country_of_origin";

    /** Rotates outcomes across consecutive scans so the demo shows all three verdicts. */
    private final AtomicInteger counter = new AtomicInteger();

    @Override
    public MlAnalyzeResponse analyze(byte[] imageBytes, String filename, String contentType, String scanId) {
        int bucket = Math.floorMod(counter.getAndIncrement(), 3);
        log.info("[dev] MockMlAnalysisClient producing bucket-{} ({}) result for scan {}",
                bucket, new String[]{"COMPLIANT", "PARTIAL", "NON_COMPLIANT"}[bucket], scanId);

        return switch (bucket) {
            case 0 -> compliant(scanId);
            case 1 -> partial(scanId);
            default -> nonCompliant(scanId);
        };
    }

    private MlAnalyzeResponse compliant(String scanId) {
        Map<String, MlDeclaration> d = new LinkedHashMap<>();
        d.put(MANUFACTURER, present("ABC Foods Pvt Ltd, MIDC Bhosari, Pune, MH 411026", 0.95));
        d.put(COMMODITY, present("Refined Sunflower Oil", 0.93));
        d.put(NET_QTY, present("Net Qty: 1 L", 0.91));
        d.put(MRP, present("MRP Rs 185.00 (inclusive of all taxes)", 0.94));
        d.put(MFG_DATE, present("Mfg: 07/2026", 0.88));
        d.put(CONSUMER_CARE, present("care@abcfoods.example | 1800-000-000", 0.86));
        d.put(COUNTRY, present("Country of Origin: India", 0.9));
        return build(scanId, "COMPLIANT", d,
                List.of(font(NET_QTY, 4.3, 4.0, true)),
                List.of());
    }

    private MlAnalyzeResponse partial(String scanId) {
        Map<String, MlDeclaration> d = new LinkedHashMap<>();
        d.put(MANUFACTURER, present("GrainMill Industries, Indore, MP", 0.90));
        d.put(COMMODITY, present("Whole Wheat Atta", 0.92));
        d.put(NET_QTY, present("5 kg", 0.87));
        d.put(MRP, present("MRP Rs 260.00", 0.62));
        d.put(MFG_DATE, present("05/2026", 0.83));
        d.put(CONSUMER_CARE, absent());
        return build(scanId, "NON COMPLIANT", d,
                List.of(font(NET_QTY, 3.7, 4.0, false)),
                List.of(
                        violation("Rule 6(1)(e)", MRP, "Missing mandatory phrase 'inclusive of all taxes'", "MINOR"),
                        violation("Rule 7", NET_QTY, "Font height 3.7mm is below required 4.0mm", "MINOR")));
    }

    private MlAnalyzeResponse nonCompliant(String scanId) {
        Map<String, MlDeclaration> d = new LinkedHashMap<>();
        d.put(MANUFACTURER, present("TangyTom", 0.71));
        d.put(COMMODITY, present("Tomato Ketchup", 0.90));
        d.put(NET_QTY, present("950 g", 0.85));
        d.put(MRP, absent());
        d.put(MFG_DATE, absent());
        d.put(CONSUMER_CARE, absent());
        return build(scanId, "NON COMPLIANT", d,
                List.of(),
                List.of(
                        violation("Rule 6(1)(a)", MANUFACTURER, "Complete address not declared (name only)", "CRITICAL"),
                        violation("Rule 6(1)(e)", MRP, "Mandatory declaration 'Maximum Retail Price' is missing", "CRITICAL"),
                        violation("Rule 6(1)(f)", MFG_DATE, "Mandatory declaration 'Month and Year of Manufacture' is missing", "MAJOR"),
                        violation("Rule 6(1)(d)", CONSUMER_CARE, "Mandatory declaration 'Consumer Care Details' is missing", "MAJOR")));
    }

    // --- helpers ---

    private MlAnalyzeResponse build(String scanId, String overall, Map<String, MlDeclaration> declarations,
                                    List<MlFontAnalysis> fonts, List<MlViolation> violations) {
        MlAnalyzeResponse r = new MlAnalyzeResponse();
        r.setProductId(scanId);
        r.setStatus("SUCCESS");
        r.setProcessedAt(Instant.now().toString());
        r.setDeclarations(declarations);
        r.setFontAnalysis(fonts);
        r.setViolations(violations);
        r.setOverallComplianceStatus(overall);

        List<String> lowConf = new ArrayList<>();
        declarations.forEach((k, v) -> {
            if (v.isPresent() && v.getConfidence() != null && v.getConfidence() < 0.85) lowConf.add(k);
        });
        MlConfidenceFlags flags = new MlConfidenceFlags();
        flags.setLowConfidenceFields(lowConf);
        flags.setNeedsManualReview(!lowConf.isEmpty() || !violations.isEmpty());
        r.setConfidenceFlags(flags);
        return r;
    }

    private MlDeclaration present(String value, double confidence) {
        MlDeclaration d = new MlDeclaration();
        d.setPresent(true);
        d.setValue(value);
        d.setConfidence(confidence);
        d.setBbox(List.of(rand(40, 300), rand(40, 520), rand(90, 260), rand(22, 56)));
        d.setSourceImageIndex(0);
        return d;
    }

    private MlDeclaration absent() {
        MlDeclaration d = new MlDeclaration();
        d.setPresent(false);
        d.setConfidence(0.0);
        return d;
    }

    private MlFontAnalysis font(String field, double measured, double required, boolean compliant) {
        MlFontAnalysis f = new MlFontAnalysis();
        f.setField(field);
        f.setMeasuredHeightMm(measured);
        f.setRequiredMinMm(required);
        f.setCompliant(compliant);
        return f;
    }

    private MlViolation violation(String ruleRef, String field, String issue, String severity) {
        MlViolation v = new MlViolation();
        v.setRuleRef(ruleRef);
        v.setField(field);
        v.setIssue(issue);
        v.setSeverity(severity);
        return v;
    }

    private int rand(int min, int max) {
        return min + (int) (Math.random() * (max - min));
    }
}
