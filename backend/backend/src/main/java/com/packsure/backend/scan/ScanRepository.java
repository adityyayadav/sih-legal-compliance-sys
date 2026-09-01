package com.packsure.backend.scan;

import com.packsure.backend.common.ComplianceStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ScanRepository extends JpaRepository<Scan, UUID> {

    // --- global (ADMIN) ---
    long countByOverallStatus(ComplianceStatus overallStatus);

    long countByCreatedAtAfter(LocalDateTime cutoff);

    // --- scoped to one inspector ---
    Page<Scan> findByScannedByEmail(String email, Pageable pageable);

    long countByScannedByEmail(String email);

    long countByOverallStatusAndScannedByEmail(ComplianceStatus overallStatus, String email);

    long countByCreatedAtAfterAndScannedByEmail(LocalDateTime cutoff, String email);

    /**
     * Detailed view: fetch the scan with its product eagerly. The two child
     * collections are left lazy on purpose — Hibernate can't join-fetch two
     * {@code List} collections at once ("cannot simultaneously fetch multiple
     * bags") — so callers must run inside a read-only transaction and touch
     * {@code declarations} / {@code complianceResults} to initialize them.
     */
    @EntityGraph(attributePaths = {"product", "scannedBy"})
    @Query("select s from Scan s where s.id = :id")
    Optional<Scan> findDetailedById(@Param("id") UUID id);
}
