from apps.api.core.ports.intelligence import (
    Evidence,
    IntelligenceQuery,
    IntelligenceResponse,
    MesaIntelligencePort,
    OperationState,
)
from apps.api.models.parser import ParsedDocument, ParsedPage
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresLexicalAdapter(MesaIntelligencePort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        try:
            # Note: We must ensure we are searching within the current tenant.
            # But the RLS guard in do_orm_execute already enforces tenant_id!
            # We just need to join ParsedDocument and ParsedPage and search.
            
            # Use websearch_to_tsquery for natural language search
            tsquery = func.websearch_to_tsquery('english', query.query_text)
            
            stmt = select(ParsedPage).join(ParsedDocument).where(
                ParsedPage.fts_vector.op("@@")(tsquery)
            ).limit(5)
            
            if query.matter_id:
                # Add matter_id filter
                # ParsedDocument -> Document -> Matter
                from apps.api.models.document import Document
                stmt = stmt.join(Document, ParsedDocument.document_id == Document.id)
                stmt = stmt.where(Document.matter_id == query.matter_id)

            result = await self.session.execute(stmt)
            pages = result.scalars().all()
            
            if not pages:
                return IntelligenceResponse(state=OperationState.no_evidence_retrieved)
                
            evidence_list = []
            for p in pages:
                # We could use ts_headline for snippet, but for now just take a slice
                snippet = p.text_content[:200] + "..." if len(p.text_content) > 200 else p.text_content
                evidence_list.append(Evidence(
                    document_id=p.parsed_document_id,
                    page_number=p.page_number,
                    text_snippet=snippet
                ))
                
            return IntelligenceResponse(
                state=OperationState.success,
                summary=f"Found {len(pages)} matching pages.",
                evidence=evidence_list
            )
        except SQLAlchemyError as e:
            return IntelligenceResponse(state=OperationState.unavailable, error_message=str(e))
