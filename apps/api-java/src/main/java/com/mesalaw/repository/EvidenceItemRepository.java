package com.mesalaw.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.mesalaw.entity.matter.EvidenceItem;

@Repository
public interface EvidenceItemRepository extends JpaRepository<EvidenceItem, String> {
    List<EvidenceItem> findByMatterIdAndTenantIdAndDeletedFalse(String matterId, String tenantId);
}
