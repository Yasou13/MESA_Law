package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.document.Document;

@Repository
public interface DocumentRepository extends JpaRepository<Document, String> {

    List<Document> findByMatterIdAndDeletedFalse(String matterId);
}
