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
        duration_histogram = meter.create_histogram("intelligence_request_duration", description="Intelligence query duration")
        failure_counter = meter.create_counter("intelligence_failures", description="Intelligence query failures")

        start_time = time.time()
        
        try:
            with tracer.start_as_current_span("intelligence_query") as span:
                span.set_attribute("query.text", query.query_text)
                if query.matter_id:
                    span.set_attribute("query.matter_id", query.matter_id)
                    
                tsquery = func.websearch_to_tsquery('turkish', query.query_text)
                
                from apps.api.models.parser import DocumentChunk
                
                stmt = select(DocumentChunk).where(
                    DocumentChunk.fts_vector.op("@@")(tsquery)
                ).limit(5)
                
                if query.matter_id:
                    from apps.api.models.document import Document
                    stmt = stmt.join(Document, DocumentChunk.document_id == Document.id)
                    stmt = stmt.where(Document.matter_id == query.matter_id)

                result = await self.session.execute(stmt)
                chunks = result.scalars().all()
                
                duration_histogram.record(time.time() - start_time, {"status": "success"})
                
                if not chunks:
                    return IntelligenceResponse(state=OperationState.no_evidence_retrieved)
                    
                evidence_list = []
                for c in chunks:
                    snippet = c.text_content[:200] + "..." if len(c.text_content) > 200 else c.text_content
                    evidence_list.append(Evidence(
                        document_id=c.document_id,
                        page_number=0, # Optional: we can join parsed_pages to get actual page_number if needed, or extract from page_id
                        text_snippet=f"{snippet}\n{c.watermarked_text}"
                    ))
                    
                return IntelligenceResponse(
                    state=OperationState.success,
                    summary=f"Found {len(chunks)} matching chunks.",
                    evidence=evidence_list
                )
        except SQLAlchemyError as e:
            failure_counter.add(1, {"reason": "sqlalchemy_error"})
            duration_histogram.record(time.time() - start_time, {"status": "failed"})
            return IntelligenceResponse(state=OperationState.unavailable, error_message=str(e))
