package com.mesalaw.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.matter.Matter;

@Repository
public interface MatterRepository extends JpaRepository<Matter, String> {

    List<Matter> findByTenantIdAndDeletedFalse(String tenantId);

    Optional<Matter> findByIdAndTenantId(String id, String tenantId);
}
