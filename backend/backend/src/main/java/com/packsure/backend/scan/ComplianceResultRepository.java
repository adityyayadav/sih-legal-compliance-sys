package com.packsure.backend.scan;

import com.packsure.backend.common.RuleStatus;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ComplianceResultRepository extends JpaRepository<ComplianceResult, UUID> {

    /** Most frequent violations, grouped by rule code. Pass {@code PageRequest.of(0, 5)} for the top 5. */
    @Query("""
            select cr.ruleCode as ruleCode, count(cr) as count
            from ComplianceResult cr
            where cr.status = :status
            group by cr.ruleCode
            order by count(cr) desc
            """)
    List<RuleCodeCount> findTopViolations(@Param("status") RuleStatus status, Pageable pageable);

    /** Projection for {@link #findTopViolations}. */
    interface RuleCodeCount {
        String getRuleCode();
        long getCount();
    }
}
