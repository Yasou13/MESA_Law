package com.mesalaw.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.matter.MatterMember;

@Repository
public interface MatterMemberRepository extends JpaRepository<MatterMember, String> {

    List<MatterMember> findByMatterId(String matterId);

    Optional<MatterMember> findByMatterIdAndUserId(String matterId, String userId);

    boolean existsByMatterIdAndUserId(String matterId, String userId);
}
