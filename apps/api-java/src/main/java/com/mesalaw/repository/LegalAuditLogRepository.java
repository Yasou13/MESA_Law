package com.mesalaw.repository;

import java.util.Collection;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.audit.LegalAuditLog;

@Repository
public interface LegalAuditLogRepository extends JpaRepository<LegalAuditLog, String> {

    List<LegalAuditLog> findByTenantIdAndMatterIdAndEntityTypeAndEntityIdAndActionInOrderByCreatedAtAsc(
            String tenantId, String matterId, String entityType, String entityId, Collection<String> actions);
}
