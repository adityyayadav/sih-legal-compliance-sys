package com.packsure.backend.scan;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ScanRepository extends JpaRepository<Scan, UUID> {
}
