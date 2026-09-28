package com.mesalaw.controller;

import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mesalaw.security.RequestContext;
import com.mesalaw.security.RequestContextHolder;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * Question-Answering endpoint for document-based Q&A.
 * Replaces Python's routers/qa.py.
 *
 * <p>The actual RAG pipeline (vector search + LLM) will be implemented
 * in a QAService — this controller handles routing and access control.</p>
 */
@RestController
@RequestMapping("/qa")
@RequiredArgsConstructor
public class QAController {

    @Data
    public static class QAQuery {
        @NotBlank private String matterId;
        private String documentId;
        @NotBlank private String question;
    }

    @Data @AllArgsConstructor
    public static class QAResponse {
        private String answer;
        private List<Map<String, Object>> sources;
        private String model;
    }

    /**
     * POST /qa/ask — Ask a question about a matter's documents.
     * Matches Python: POST /qa/ask → askQuestion
     */
    @PostMapping("/ask")
    public QAResponse askQuestion(@Valid @RequestBody QAQuery query) {
        RequestContext ctx = RequestContextHolder.get();

        // TODO: Implement RAG pipeline:
        // 1. Retrieve relevant chunks from DocumentChunk using vector search / FTS
        // 2. Build context from matched chunks
        // 3. Send to LLM (OpenAI/Anthropic/Gemini) via LlmClient
        // 4. Return answer with source citations

        return new QAResponse(
                "QA pipeline not yet implemented. This endpoint will use vector search + LLM to answer questions about matter documents.",
                List.of(),
                "mock"
        );
    }
}
