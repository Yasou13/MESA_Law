package com.mesalaw.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.deadline.ApprovedDeadline;

@Repository
public interface ApprovedDeadlineRepository extends JpaRepository<ApprovedDeadline, String> {

    List<ApprovedDeadline> findByTenantIdAndCompletedFalseOrderByDueDateAsc(String tenantId);

    List<ApprovedDeadline> findByMatterIdAndCompletedFalseOrderByDueDateAsc(String matterId);

    List<ApprovedDeadline> findByTenantIdAndMatterIdAndCompletedFalseOrderByDueDateAsc(
            String tenantId, String matterId);

    Optional<ApprovedDeadline> findByIdAndTenantId(String id, String tenantId);

    /** Open deadlines across all matters the user is a member of (matches the Python MatterMember join). */
    @Query("""
            SELECT d FROM ApprovedDeadline d
            WHERE d.tenantId = :tenantId
              AND d.completed = false
              AND d.matterId IN (
                  SELECT m.matterId FROM MatterMember m
                  WHERE m.userId = :userId AND m.tenantId = :tenantId AND m.deleted = false)
            ORDER BY d.dueDate ASC
            """)
    List<ApprovedDeadline> findOpenForMember(@Param("tenantId") String tenantId, @Param("userId") String userId);
}
