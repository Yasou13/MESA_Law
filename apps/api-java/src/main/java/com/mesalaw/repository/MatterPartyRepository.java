package com.mesalaw.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.mesalaw.entity.matter.MatterParty;

@Repository
public interface MatterPartyRepository extends JpaRepository<MatterParty, String> {
    List<MatterParty> findByMatterIdAndTenantIdAndDeletedFalse(String matterId, String tenantId);
}
