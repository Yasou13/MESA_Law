package com.mesalaw.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.mesalaw.entity.matter.Claim;

@Repository
public interface ClaimRepository extends JpaRepository<Claim, String> {
    List<Claim> findByMatterIdAndTenantIdAndDeletedFalse(String matterId, String tenantId);
}
