package com.mesalaw.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.review.ExtractionSuggestion;

@Repository
public interface ExtractionSuggestionRepository extends JpaRepository<ExtractionSuggestion, String> {

    Optional<ExtractionSuggestion> findByIdAndTenantId(String id, String tenantId);

    Optional<ExtractionSuggestion> findByIdAndTenantIdAndMatterId(String id, String tenantId, String matterId);
}
