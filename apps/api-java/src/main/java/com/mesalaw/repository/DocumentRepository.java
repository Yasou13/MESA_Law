package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.document.Document;

@Repository
public interface DocumentRepository extends JpaRepository<Document, String> {

    List<Document> findByMatterIdAndDeletedFalse(String matterId);

    List<Document> findByMatterIdAndTenantIdAndDeletedFalse(String matterId, String tenantId);

    @Query("""
            select distinct d from Document d
            join MatterMember mm on mm.matterId = d.matterId
            where d.tenantId = :tenantId
              and d.deleted = false
              and mm.tenantId = :tenantId
              and mm.userId = :userId
              and mm.deleted = false
            order by d.createdAt desc
            """)
    List<Document> findAccessibleDocuments(@Param("tenantId") String tenantId,
            @Param("userId") String userId);
}
