package com.packsure.backend.report.service;

import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.FontFactory;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;
import com.packsure.backend.exception.ResourceNotFoundException;
import com.packsure.backend.scan.ComplianceResult;
import com.packsure.backend.scan.Declaration;
import com.packsure.backend.scan.Scan;
import com.packsure.backend.scan.ScanRepository;
import com.packsure.backend.scan.service.ScanQueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PdfReportService {

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
    private static final Font H1 = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 16);
    private static final Font H2 = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 12);
    private static final Font TH = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 9, Color.WHITE);
    private static final Font TD = FontFactory.getFont(FontFactory.HELVETICA, 9);
    private static final Font LABEL = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 10);
    private static final Font VALUE = FontFactory.getFont(FontFactory.HELVETICA, 10);
    private static final Color HEADER_BG = new Color(51, 51, 51);

    private final ScanRepository scanRepository;

    @Transactional(readOnly = true)
    public byte[] generate(UUID scanId, String requesterEmail, boolean admin) {
        Scan scan = scanRepository.findDetailedById(scanId)
                .orElseThrow(() -> new ResourceNotFoundException("Scan not found"));
        ScanQueryService.assertVisible(scan, requesterEmail, admin);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        Document doc = new Document(PageSize.A4, 40, 40, 50, 40);
        try {
            PdfWriter.getInstance(doc, out);
            doc.open();

            Paragraph title = new Paragraph("Legal Metrology Compliance Report", H1);
            title.setAlignment(Element.ALIGN_CENTER);
            title.setSpacingAfter(16f);
            doc.add(title);

            doc.add(metaTable(scan));
            doc.add(spacer());

            doc.add(new Paragraph("Declarations", H2));
            doc.add(declarationsTable(scan));
            doc.add(spacer());

            doc.add(new Paragraph("Compliance Results", H2));
            doc.add(complianceTable(scan));
            doc.add(spacer());

            Paragraph footer = new Paragraph(
                    "Overall compliance status: "
                            + (scan.getOverallStatus() != null ? scan.getOverallStatus().name() : "N/A"),
                    H2);
            footer.setAlignment(Element.ALIGN_RIGHT);
            doc.add(footer);

            doc.close();
        } catch (DocumentException e) {
            throw new IllegalStateException("Failed to generate PDF report for scan " + scanId, e);
        }
        return out.toByteArray();
    }

    private PdfPTable metaTable(Scan scan) {
        PdfPTable t = new PdfPTable(new float[]{1f, 3f});
        t.setWidthPercentage(100);
        var product = scan.getProduct();
        kv(t, "Scan ID", String.valueOf(scan.getId()));
        kv(t, "Scan date", scan.getCreatedAt() != null ? scan.getCreatedAt().format(DATE_FMT) : "-");
        kv(t, "Processed at", scan.getProcessedAt() != null ? scan.getProcessedAt().format(DATE_FMT) : "-");
        kv(t, "Scan status", scan.getStatus() != null ? scan.getStatus().name() : "-");
        kv(t, "Product", product != null ? nullSafe(product.getName()) : "-");
        kv(t, "Category", product != null ? nullSafe(product.getCategory()) : "-");
        kv(t, "Brand", product != null ? nullSafe(product.getBrand()) : "-");
        return t;
    }

    private PdfPTable declarationsTable(Scan scan) {
        PdfPTable t = new PdfPTable(new float[]{2.5f, 1f, 3.5f, 1.2f});
        t.setWidthPercentage(100);
        header(t, "Declaration Type", "Present", "Extracted Value", "Confidence");
        if (scan.getDeclarations().isEmpty()) {
            emptyRow(t, 4, "No declarations extracted");
        } else {
            for (Declaration d : scan.getDeclarations()) {
                cell(t, nullSafe(d.getDeclarationType()));
                cell(t, d.isPresent() ? "Yes" : "No");
                cell(t, nullSafe(d.getExtractedValue()));
                cell(t, d.getConfidenceScore() != null ? String.format("%.2f", d.getConfidenceScore()) : "-");
            }
        }
        return t;
    }

    private PdfPTable complianceTable(Scan scan) {
        PdfPTable t = new PdfPTable(new float[]{2f, 3.5f, 1.2f, 3f});
        t.setWidthPercentage(100);
        header(t, "Rule Code", "Description", "Status", "Remarks");
        if (scan.getComplianceResults().isEmpty()) {
            emptyRow(t, 4, "No compliance results");
        } else {
            for (ComplianceResult cr : scan.getComplianceResults()) {
                cell(t, nullSafe(cr.getRuleCode()));
                cell(t, nullSafe(cr.getRuleDescription()));
                cell(t, cr.getStatus() != null ? cr.getStatus().name() : "-");
                cell(t, nullSafe(cr.getRemarks()));
            }
        }
        return t;
    }

    private void kv(PdfPTable t, String label, String value) {
        t.addCell(borderlessCell(new Phrase(label, LABEL)));
        t.addCell(borderlessCell(new Phrase(value, VALUE)));
    }

    private void header(PdfPTable t, String... titles) {
        for (String title : titles) {
            PdfPCell c = new PdfPCell(new Phrase(title, TH));
            c.setBackgroundColor(HEADER_BG);
            c.setPadding(5f);
            t.addCell(c);
        }
    }

    private void cell(PdfPTable t, String text) {
        PdfPCell c = new PdfPCell(new Phrase(text, TD));
        c.setPadding(4f);
        t.addCell(c);
    }

    private void emptyRow(PdfPTable t, int colspan, String text) {
        PdfPCell c = new PdfPCell(new Phrase(text, TD));
        c.setColspan(colspan);
        c.setPadding(4f);
        t.addCell(c);
    }

    private PdfPCell borderlessCell(Phrase p) {
        PdfPCell c = new PdfPCell(p);
        c.setBorder(0);
        c.setPadding(3f);
        return c;
    }

    private Paragraph spacer() {
        Paragraph p = new Paragraph(" ");
        p.setSpacingAfter(10f);
        return p;
    }

    private String nullSafe(String s) {
        return s == null || s.isBlank() ? "-" : s;
    }
}
