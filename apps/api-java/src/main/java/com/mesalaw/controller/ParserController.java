package com.mesalaw.controller;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.dto.ParsedDocumentDto.ParsedDocumentResponse;
import com.mesalaw.dto.ParsedDocumentDto.ParsedPageResponse;
import com.mesalaw.entity.document.ParsedDocument;
import com.mesalaw.entity.document.ParsedPage;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.persistence.EntityManager;
import lombok.RequiredArgsConstructor;

/**
 * Parsed document / page viewer endpoints.
 * Replaces Python's routers/parser.py.
 */
@RestController
@RequestMapping("/parsed")
@RequiredArgsConstructor
public class ParserController {

    private final EntityManager entityManager;
    private final ObjectMapper objectMapper;

    /**
     * GET /parsed/document/{documentId} — List parsed documents for a document.
     * Matches Python: GET /parsed/document/{document_id} → listParsedDocuments
     */
    @GetMapping("/document/{documentId}")
    public List<ParsedDocumentResponse> listParsedDocuments(@PathVariable String documentId) {
        RequestContext ctx = RequestContextHolder.get();
        List<ParsedDocument> docs = entityManager.createQuery(
                "SELECT p FROM ParsedDocument p WHERE p.documentId = :did AND p.tenantId = :tid ORDER BY p.parsingRevision DESC",
                ParsedDocument.class)
                .setParameter("did", documentId).setParameter("tid", ctx.tenantId())
                .getResultList();

        return docs.stream().map(d -> new ParsedDocumentResponse(
                d.getId(), d.getDocumentId(), d.getRevisionId(),
                d.getParsingRevision(), d.getParserUsed(), d.getStatus())).collect(Collectors.toList());
    }

    /**
     * GET /parsed/{parsedDocumentId}/pages — List pages of a parsed document.
     * Matches Python: GET /parsed/{parsed_document_id}/pages → listParsedPages
     */
    @GetMapping("/{parsedDocumentId}/pages")
    public List<ParsedPageResponse> listParsedPages(@PathVariable String parsedDocumentId) {
        RequestContext ctx = RequestContextHolder.get();

        // Verify parsed document belongs to tenant
        ParsedDocument pdoc = entityManager.find(ParsedDocument.class, parsedDocumentId);
        if (pdoc == null || !pdoc.getTenantId().equals(ctx.tenantId())) {
            throw new ProblemException(404, "Not Found", "Parsed document not found");
        }

        List<ParsedPage> pages = entityManager.createQuery(
                "SELECT p FROM ParsedPage p WHERE p.parsedDocumentId = :pdid ORDER BY p.pageNumber ASC",
                ParsedPage.class)
                .setParameter("pdid", parsedDocumentId)
                .getResultList();

        return pages.stream().map(this::toResponse).collect(Collectors.toList());
    }

    private ParsedPageResponse toResponse(ParsedPage page) {
        JsonNode layoutData = null;
        if (page.getLayoutData() != null) {
            try {
                layoutData = objectMapper.readTree(page.getLayoutData());
            } catch (JsonProcessingException e) {
                throw new IllegalStateException("Stored parsed-page layout data is invalid JSON", e);
            }
        }
        return new ParsedPageResponse(page.getId(), page.getPageNumber(), page.getTextContent(), layoutData);
    }
}
