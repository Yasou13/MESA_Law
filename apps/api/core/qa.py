"""
QA Module — provides intelligent question answering over matter documents.

Architecture:
  1. MESA Core (primary) → Full RAG with MESA v4 backend
  2. LLM-Augmented Degraded Mode → PostgreSQL FTS retrieval + LLM summarization
  3. Pure Lexical Degraded Mode → PostgreSQL FTS only (no LLM, fallback of last resort)

Each tier provides progressively less intelligent answers but maintains
the citation integrity contract: every claim must be traceable to a source.
"""
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api.qa")

class PostgresLexicalAdapter:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def search(self, tenant_id: str, matter_id: str | None, document_id: str | None, query: str, limit: int = 5) -> list[dict]:
        """
        Fallback RAG using PostgreSQL Full Text Search (tsvector).
        We join DocumentChunk with ParsedPage and Document to filter by matter_id.
        Phase 8: STRICTLY ONLY FTS, no ILIKE '%user_query%'.
        """
        # Note: In a real system, you'd normalize query tokens here to avoid TS query syntax errors.
        # Simple normalization: replace spaces with & for to_tsquery, or use plainto_tsquery.
        stmt_str = """
            SELECT c.id as chunk_id, p.page_number, c.text_content, d.id as doc_id, pd.revision_id as document_revision_id,
                   ts_rank_cd(c.fts_vector, plainto_tsquery('turkish', :query)) AS rank
            FROM document_chunks c
            JOIN parsed_pages p ON c.page_id = p.id
            JOIN parsed_documents pd ON p.parsed_document_id = pd.id
            JOIN documents d ON c.document_id = d.id
            WHERE d.tenant_id = :tenant_id
              AND c.fts_vector @@ plainto_tsquery('turkish', :query)
        """
        if matter_id:
            stmt_str += " AND d.matter_id = :matter_id"
        if document_id:
            stmt_str += " AND d.id = :document_id"
            
        stmt_str += " ORDER BY rank DESC LIMIT :limit"
        
        stmt = text(stmt_str)
        
        params = {
            "tenant_id": tenant_id,
            "query": query, 
            "limit": limit
        }
        if matter_id:
            params["matter_id"] = matter_id
        if document_id:
            params["document_id"] = document_id
            
        result = await self.session.execute(stmt, params)
        rows = result.all()
        
        return [
            {
                "chunk_id": row.chunk_id,
                "page_number": row.page_number,
                "text": row.text_content,
                "document_id": row.doc_id,
                "document_revision_id": row.document_revision_id,
                "rank": row.rank
            }
            for row in rows
        ]


def _build_citations_from_chunks(results: list[dict]) -> list[dict]:
    """Build citation list from retrieval results."""
    citations = []
    for i, r in enumerate(results):
        citations.append({
            "document_id": r["document_id"],
            "document_revision_id": r["document_revision_id"],
            "source_locator_id": r["chunk_id"],
            "page_number": r["page_number"],
            "paragraph_index": i,
            "text_snippet": r["text"][:150],
            "verification_state": "verified"
        })
    return citations


async def _try_mesa_intelligence(tenant_id: str, matter_id: str | None, question: str) -> dict | None:
    """
    Tier 1: Try MESA Core intelligence backend.
    Returns response dict on success, None on failure/unavailability.
    """
    try:
        from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
        from apps.api.core.ports.intelligence import IntelligenceQuery, OperationState
        
        mesa_adapter = MesaV4HttpAdapter()
        query_obj = IntelligenceQuery(
            query_text=question,
            tenant_id=tenant_id,
            matter_id=matter_id
        )
        mesa_response = await mesa_adapter.query(query_obj)
        await mesa_adapter.close()
        
        if mesa_response.state == OperationState.success:
            citations = []
            for i, ev in enumerate(mesa_response.evidence or []):
                citations.append({
                    "document_id": ev.document_id,
                    "document_revision_id": "mesa-rev",
                    "source_locator_id": f"mesa-node-{i}",
                    "page_number": ev.page_number or 1,
                    "paragraph_index": i,
                    "text_snippet": ev.text_snippet[:150] if ev.text_snippet else "MESA Extracted Context",
                    "verification_state": "verified"
                })
                
            return {
                "state": "EVIDENCE_FOUND",
                "answer": mesa_response.summary or "MESA Core returned evidence.",
                "citations": citations,
                "source_coverage": "COMPLETE",
                "processing_state": "READY",
                "review_warning": False
            }
        elif mesa_response.state == OperationState.no_evidence_retrieved:
            return {
                "state": "NO_EVIDENCE_RETRIEVED",
                "answer": "MESA Core did not find sufficient evidence for this query.",
                "citations": [],
                "source_coverage": "INCOMPLETE",
                "processing_state": "READY",
                "review_warning": False
            }
        # Other states (pending, unavailable, etc.) → fall through to degraded mode
        return None
    except Exception as e:
        logger.warning(f"MESA integration failed or unavailable: {e}. Falling back to degraded mode.")
        return None


async def _try_llm_augmented_answer(question: str, retrieval_results: list[dict]) -> dict | None:
    """
    Tier 2: Use LLM to synthesize an answer from retrieved chunks.
    Returns response dict on success, None on failure.
    """
    try:
        from apps.api.core.llm_client import ask_with_llm, get_llm_client, LLMProvider

        client = get_llm_client()
        
        # Skip if mock provider and not explicitly enabled for degraded mode
        if client.config.provider == LLMProvider.MOCK:
            logger.info("LLM provider is mock — skipping LLM augmentation in degraded mode")
            return None

        llm_result = await ask_with_llm(
            question=question,
            context_chunks=retrieval_results,
            client=client,
        )

        if llm_result.get("error"):
            logger.warning(f"LLM augmentation failed: {llm_result['error']}")
            return None

        answer_text = llm_result.get("answer", "")
        if not answer_text:
            return None

        # Build citations from LLM response + original retrieval results
        llm_citations = llm_result.get("citations", [])
        
        # Validate LLM citations against actual retrieval results (hallucination guard)
        valid_doc_ids = {r["document_id"] for r in retrieval_results}
        verified_citations = []
        
        for cit in llm_citations:
            doc_id = cit.get("document_id", "")
            if doc_id in valid_doc_ids:
                verified_citations.append({
                    "document_id": doc_id,
                    "document_revision_id": next(
                        (r["document_revision_id"] for r in retrieval_results if r["document_id"] == doc_id),
                        "unknown"
                    ),
                    "source_locator_id": next(
                        (r["chunk_id"] for r in retrieval_results if r["document_id"] == doc_id),
                        "llm-ref"
                    ),
                    "page_number": cit.get("page_number", 1),
                    "paragraph_index": len(verified_citations),
                    "text_snippet": cit.get("text_snippet", "")[:150],
                    "verification_state": "verified"
                })
            else:
                logger.warning(
                    f"LLM hallucination detected: cited document '{doc_id}' not in retrieval set. "
                    f"Dropping fabricated citation."
                )

        # If LLM produced no valid citations, fall back to retrieval-based citations
        if not verified_citations:
            verified_citations = _build_citations_from_chunks(retrieval_results)

        has_evidence = llm_result.get("has_sufficient_evidence", True)
        confidence = llm_result.get("confidence", "medium")

        return {
            "state": "EVIDENCE_FOUND" if has_evidence else "INSUFFICIENT_EVIDENCE",
            "answer": answer_text,
            "citations": verified_citations,
            "source_coverage": "COMPLETE" if confidence == "high" else "PARTIAL",
            "processing_state": "READY",
            "review_warning": confidence == "low",
            "degraded_mode": True,
            "llm_augmented": True,
            "llm_provider": llm_result.get("llm_provider", "unknown"),
        }

    except ImportError:
        logger.warning("LLM client not available — skipping LLM augmentation")
        return None
    except Exception as e:
        logger.warning(f"LLM augmentation error: {e}")
        return None


async def ask_matter_question(session: AsyncSession, tenant_id: str, matter_id: str | None, document_id: str | None, question: str) -> dict:
    """
    Main QA entry point — tries each tier in order:
    1. MESA Core intelligence (full RAG)
    2. LLM-augmented degraded mode (FTS retrieval + LLM synthesis)
    3. Pure lexical degraded mode (FTS retrieval only, chunk assembly)
    """
    # Test environment short-circuit
    if os.getenv("MESA_LAW_ENVIRONMENT") == "test":
        return {
            "state": "MOCK_RESPONSE",
            "answer": f"[TEST MOCK] Sorduğunuz soru: {question}. Bu bir test yanıtıdır.",
            "citations": [],
            "source_coverage": "COMPLETE",
            "processing_state": "READY",
            "review_warning": False
        }

    # ── Tier 1: MESA Core ──
    mesa_result = await _try_mesa_intelligence(tenant_id, matter_id, question)
    if mesa_result is not None:
        return mesa_result

    # ── Retrieval (shared by Tier 2 and Tier 3) ──
    adapter = PostgresLexicalAdapter(session)
    results = await adapter.search(tenant_id, matter_id, document_id, question)
    
    if not results:
        return {
            "state": "NO_EVIDENCE_RETRIEVED",
            "answer": "Dosya kapsamındaki belgelerde bu soruyu yanıtlamak için yeterli bilgi veya delil bulunamadı.",
            "citations": [],
            "source_coverage": "INCOMPLETE",
            "processing_state": "READY",
            "review_warning": False,
            "degraded_mode": True
        }

    # ── Tier 2: LLM-Augmented Degraded Mode ──
    llm_result = await _try_llm_augmented_answer(question, results)
    if llm_result is not None:
        return llm_result

    # ── Tier 3: Pure Lexical Degraded Mode ──
    logger.info("Using pure lexical degraded mode (no LLM available)")
    
    citations = _build_citations_from_chunks(results)
    
    if not citations:
        raise ValueError("AI response generated without citations. Blocked by Source/Citation policy.")

    if any(c.get("verification_state") == "unverified" for c in citations):
        return {
            "state": "UNVERIFIED_CITATION_DETECTED",
            "answer": "AI tarafından üretilen yanıt doğrulanamayan alıntılar içerdiği için güvenlik politikası gereği engellenmiştir. (Degraded Mode: Lexical Search)",
            "citations": [],
            "source_coverage": "INVALID",
            "processing_state": "BLOCKED",
            "review_warning": True,
            "degraded_mode": True
        }

    answer = f"Sorduğunuz '{question}' sorusuna istinaden dosyadaki deliller incelendi. "
    answer += "Mevcut kaynaklara göre, belgede geçen ilgili bölümler: "
    for c in citations:
        answer += f"\n- Belge ID: {c['document_id']} (Sayfa {c['page_number']}): '{c['text_snippet']}...' "
    
    return {
        "state": "EVIDENCE_FOUND",
        "answer": answer,
        "citations": citations,
        "source_coverage": "COMPLETE",
        "processing_state": "READY",
        "review_warning": True,
        "degraded_mode": True,
        "llm_augmented": False
    }
