package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.draft.Draft;

@Repository
public interface DraftRepository extends JpaRepository<Draft, String> {

    List<Draft> findByTenantIdAndMatterIdAndDeletedFalse(String tenantId, String matterId);

    /**
     * List all non-deleted drafts visible to the given user within a tenant.
     * Filters by MatterMember JOIN so users only see drafts for their assigned matters.
     */
    @Query("""
            SELECT d FROM Draft d
            JOIN MatterMember mm ON mm.matterId = d.matterId
            WHERE d.tenantId = :tenantId
              AND mm.userId = :userId
              AND mm.tenantId = :tenantId
              AND d.deleted = false
            ORDER BY d.updatedAt DESC
            """)
    List<Draft> findAllByTenantAndUser(String tenantId, String userId);
}
