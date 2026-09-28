package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.draft.Draft;

@Repository
public interface DraftRepository extends JpaRepository<Draft, String> {

    List<Draft> findByTenantIdAndMatterIdAndDeletedFalse(String tenantId, String matterId);
}
