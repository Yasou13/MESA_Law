package com.mesalaw.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.draft.DraftRevision;

@Repository
public interface DraftRevisionRepository extends JpaRepository<DraftRevision, String> {
}
