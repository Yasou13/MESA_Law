package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.audit.AuditEvent;

@Repository
public interface AuditEventRepository extends JpaRepository<AuditEvent, String> {

    List<AuditEvent> findByTenantIdOrderByTimestampDesc(String tenantId);
}
