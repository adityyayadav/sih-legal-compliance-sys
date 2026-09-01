package com.packsure.backend.scan;

import com.packsure.backend.common.ScanStatus;
import org.springframework.data.jpa.domain.Specification;

import java.time.LocalDate;
import java.util.UUID;

/** Composable filters for {@code GET /api/scans}. */
public final class ScanSpecifications {

    private ScanSpecifications() {
    }

    public static Specification<Scan> ownedBy(String email) {
        return (root, query, cb) -> cb.equal(root.get("scannedBy").get("email"), email);
    }

    public static Specification<Scan> hasStatus(ScanStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }

    public static Specification<Scan> hasProduct(UUID productId) {
        return (root, query, cb) -> cb.equal(root.get("product").get("id"), productId);
    }

    public static Specification<Scan> createdFrom(LocalDate from) {
        return (root, query, cb) -> cb.greaterThanOrEqualTo(root.get("createdAt"), from.atStartOfDay());
    }

    public static Specification<Scan> createdTo(LocalDate to) {
        return (root, query, cb) -> cb.lessThan(root.get("createdAt"), to.plusDays(1).atStartOfDay());
    }
}
