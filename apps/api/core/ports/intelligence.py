from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


class OperationState(str, Enum):
    success = "success"
    pending = "pending"
    unavailable = "unavailable"
    projection_delayed = "projection_delayed"
    no_evidence_retrieved = "no_evidence_retrieved"
    source_set_incomplete = "source_set_incomplete"
    stale_source = "stale_source"

class Evidence(BaseModel):
    document_id: str
    page_number: int
    text_snippet: str

class IntelligenceQuery(BaseModel):
    tenant_id: str
    query_text: str
    matter_id: str | None = None

class IntelligenceResponse(BaseModel):
    state: OperationState
    evidence: list[Evidence] = []
    summary: str | None = None
    error_message: str | None = None

class MesaIntelligencePort(ABC):
    @abstractmethod
    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        """
        Executes an intelligence query and returns a response.
        """
