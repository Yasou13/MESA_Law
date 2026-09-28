package com.mesalaw.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.auth.Firm;

@Repository
public interface FirmRepository extends JpaRepository<Firm, String> {
}
