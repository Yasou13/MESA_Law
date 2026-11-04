package com.mesalaw.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.review.ReviewItem;

@Repository
public interface ReviewItemRepository extends JpaRepository<ReviewItem, String>,
        JpaSpecificationExecutor<ReviewItem> {

    List<ReviewItem> findByTenantIdAndMatterIdOrderByCreatedAtDesc(String tenantId, String matterId);

    List<ReviewItem> findByTenantIdAndMatterIdAndStatus(String tenantId, String matterId,
                                                        com.mesalaw.entity.review.ReviewState status);

    Optional<ReviewItem> findByIdAndTenantId(String id, String tenantId);
}
