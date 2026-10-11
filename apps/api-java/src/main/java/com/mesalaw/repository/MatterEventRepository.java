package com.mesalaw.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.mesalaw.entity.matter.MatterEvent;

@Repository
public interface MatterEventRepository extends JpaRepository<MatterEvent, String> {
    List<MatterEvent> findByMatterIdAndTenantIdAndDeletedFalseOrderByEventDateAsc(String matterId, String tenantId);
}
