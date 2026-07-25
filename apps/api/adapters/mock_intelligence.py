from apps.api.core.ports.intelligence import (
    MesaIntelligencePort, IntelligenceQuery, IntelligenceResponse, OperationState, Evidence
)

class MockMesaAdapter(MesaIntelligencePort):
    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        # Fixture routing based on query text
        q = query.query_text.lower()
        
        if "pending" in q:
            return IntelligenceResponse(state=OperationState.pending)
        elif "unavailable" in q:
            return IntelligenceResponse(state=OperationState.unavailable, error_message="Service is offline")
        elif "delayed" in q:
            return IntelligenceResponse(state=OperationState.projection_delayed)
        elif "no evidence" in q:
            return IntelligenceResponse(state=OperationState.no_evidence_retrieved)
        elif "incomplete" in q:
            return IntelligenceResponse(state=OperationState.source_set_incomplete)
        elif "stale" in q:
            return IntelligenceResponse(state=OperationState.stale_source)
            
        # Default success
        return IntelligenceResponse(
            state=OperationState.success,
            summary="Mock analysis completed.",
            evidence=[
                Evidence(document_id="mock-doc-1", page_number=1, text_snippet="Mock evidence 1")
            ]
        )
