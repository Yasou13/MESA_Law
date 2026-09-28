package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.audit.Notification;

@Repository
public interface NotificationRepository extends JpaRepository<Notification, String> {

    List<Notification> findByTenantIdAndUserIdOrderByTimestampDesc(String tenantId, String userId);

    List<Notification> findByTenantIdAndUserIdAndStatus(String tenantId, String userId, String status);
}
