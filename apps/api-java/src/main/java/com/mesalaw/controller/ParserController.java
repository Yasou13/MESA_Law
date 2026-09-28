package com.mesalaw.controller;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.entity.document.ParsedDocument;
import com.mesalaw.entity.document.ParsedPage;
import com.mesalaw.exception.ProblemException;
import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.persistence.EntityManager;
import lombok.AllArgsConstructor;
import lombok.Data;
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

    @Data @AllArgsConstructor
    public static class ParsedDocumentResponse {
        private String id, documentId, revisionId;
        private int parsingRevision;
        private String parserUsed, status;
    }

    @Data @AllArgsConstructor
    public static class ParsedPageResponse {
        private String id;
        private int pageNumber;
        private String textContent;
        private String layoutData;
    }

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
                d.getParsingRevision(), d.getParserUsed(), d.getStatus()
        )).collect(Collectors.toList());
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

        return pages.stream().map(p -> new ParsedPageResponse(
                p.getId(), p.getPageNumber(), p.getTextContent(), p.getLayoutData()
        )).collect(Collectors.toList());
    }
}
