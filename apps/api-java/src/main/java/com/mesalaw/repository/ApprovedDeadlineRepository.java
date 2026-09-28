package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.deadline.ApprovedDeadline;

@Repository
public interface ApprovedDeadlineRepository extends JpaRepository<ApprovedDeadline, String> {

    List<ApprovedDeadline> findByTenantIdAndCompletedFalseOrderByDueDateAsc(String tenantId);

    List<ApprovedDeadline> findByMatterIdAndCompletedFalseOrderByDueDateAsc(String matterId);
}
