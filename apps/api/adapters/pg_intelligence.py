from apps.api.core.ports.intelligence import (
    Evidence,
    IntelligenceQuery,
    IntelligenceResponse,
    MesaIntelligencePort,
    OperationState,
)
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresLexicalAdapter(MesaIntelligencePort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        import time

        from apps.api.core.observability import get_meter
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)
        meter = get_meter("mesa.intelligence")
        duration_histogram = meter.create_histogram(
            "intelligence_request_duration", description="Intelligence query duration"
        )
        failure_counter = meter.create_counter(
            "intelligence_failures", description="Intelligence query failures"
        )

        start_time = time.time()

        try:
            with tracer.start_as_current_span("intelligence_query") as span:
                span.set_attribute("query.text", query.query_text)
                if query.matter_id:
                    span.set_attribute("query.matter_id", query.matter_id)

                tsquery = func.websearch_to_tsquery("turkish", query.query_text)

                from apps.api.models.parser import DocumentChunk, ParsedPage

                stmt = (
                    select(DocumentChunk, ParsedPage)
                    .join(ParsedPage, DocumentChunk.page_id == ParsedPage.id)
                    .where(
                        DocumentChunk.tenant_id == query.tenant_id,
                        DocumentChunk.fts_vector.op("@@")(tsquery),
                    )
                    .limit(5)
                )

                if query.matter_id:
                    from apps.api.models.document import Document

                    stmt = stmt.join(Document, DocumentChunk.document_id == Document.id)
                    stmt = stmt.where(Document.matter_id == query.matter_id)

                result = await self.session.execute(stmt)
                rows = result.all()

                duration_histogram.record(
                    time.time() - start_time, {"status": "success"}
                )

                if not rows:
                    return IntelligenceResponse(
                        state=OperationState.no_evidence_retrieved
                    )

                evidence_list = []
                for chunk, page in rows:
                    if not chunk.revision_id:
                        continue
                    snippet = (
                        chunk.text_content[:200] + "..."
                        if len(chunk.text_content) > 200
                        else chunk.text_content
                    )
                    matter_scope = query.matter_id or "unscoped"
                    evidence_list.append(
                        Evidence(
                            dataset_id=(
                                query.dataset_ids[0]
                                if query.dataset_ids
                                else f"local-canonical:{query.tenant_id}"
                            ),
                            document_id=chunk.document_id,
                            revision_id=chunk.revision_id,
                            chunk_id=chunk.id,
                            source_ref=(
                                f"mesa-law://{query.tenant_id}/{matter_scope}/"
                                f"{chunk.document_id}/{chunk.revision_id}/{chunk.id}"
                            ),
                            evidence_span=chunk.text_content,
                            page_number=(
                                None
                                if chunk.provenance_state == "LOW_PROVENANCE"
                                else page.page_number
                            ),
                            text_snippet=snippet,
                            metadata={
                                "character_start": chunk.character_start,
                                "character_end": chunk.character_end,
                                "content_sha256": chunk.content_sha256,
                                "provenance_state": chunk.provenance_state,
                                "source": "LOCAL_CANONICAL",
                            },
                        )
                    )

                if not evidence_list:
                    return IntelligenceResponse(
                        state=OperationState.no_evidence_retrieved
                    )

                return IntelligenceResponse(
                    state=OperationState.success,
                    summary=f"Found {len(evidence_list)} matching chunks.",
                    evidence=evidence_list,
                )
        except SQLAlchemyError as e:
            failure_counter.add(1, {"reason": "sqlalchemy_error"})
            duration_histogram.record(time.time() - start_time, {"status": "failed"})
            return IntelligenceResponse(
                state=OperationState.unavailable, error_message=str(e)
            )
