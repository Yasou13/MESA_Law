package com.mesalaw.repository;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.mesalaw.entity.matter.ClaimEvidenceLink;

@Repository
public interface ClaimEvidenceLinkRepository extends JpaRepository<ClaimEvidenceLink, String> {
    List<ClaimEvidenceLink> findByClaimIdInAndTenantIdAndDeletedFalse(List<String> claimIds, String tenantId);
}
