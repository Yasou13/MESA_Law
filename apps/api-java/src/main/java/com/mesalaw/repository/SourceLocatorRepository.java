package com.mesalaw.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.document.SourceLocator;

@Repository
public interface SourceLocatorRepository extends JpaRepository<SourceLocator, String> {

    Optional<SourceLocator> findByIdAndTenantIdAndMatterIdAndDocumentIdAndDocumentRevisionId(
            String id, String tenantId, String matterId, String documentId, String documentRevisionId);
}
