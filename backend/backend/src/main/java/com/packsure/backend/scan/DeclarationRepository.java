package com.packsure.backend.scan;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface DeclarationRepository extends JpaRepository<Declaration, UUID> {
}
