package com.mesalaw.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.auth.Membership;

@Repository
public interface MembershipRepository extends JpaRepository<Membership, String> {

    List<Membership> findByUserIdAndActiveTrue(String userId);

    List<Membership> findByFirmId(String firmId);

    Optional<Membership> findByUserIdAndFirmId(String userId, String firmId);

    Optional<Membership> findFirstByUserIdAndActiveTrueOrderByCreatedAtAsc(String userId);

    boolean existsByUserIdAndFirmIdAndActiveTrue(String userId, String firmId);
}
