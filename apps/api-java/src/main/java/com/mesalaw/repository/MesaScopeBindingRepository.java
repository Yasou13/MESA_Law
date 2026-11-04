package com.mesalaw.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.mesa.MesaScopeBinding;

@Repository
public interface MesaScopeBindingRepository extends JpaRepository<MesaScopeBinding, String> {

    Optional<MesaScopeBinding> findByTenantIdAndMatterId(String tenantId, String matterId);

    boolean existsByTenantIdAndMatterId(String tenantId, String matterId);

    boolean existsByTenantIdAndDatasetId(String tenantId, String datasetId);
}
