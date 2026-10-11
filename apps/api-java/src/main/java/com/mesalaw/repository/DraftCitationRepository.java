package com.mesalaw.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mesalaw.entity.draft.DraftCitation;

@Repository
public interface DraftCitationRepository extends JpaRepository<DraftCitation, String> {

    List<DraftCitation> findByDraftId(String draftId);

    List<DraftCitation> findByDraftIdAndVerificationStateIn(String draftId, List<String> states);
}
