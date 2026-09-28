package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.document.DocumentRevision;

@Repository
public interface DocumentRevisionRepository extends JpaRepository<DocumentRevision, String> {

    List<DocumentRevision> findByDocumentIdOrderByVersionDesc(String documentId);
}
