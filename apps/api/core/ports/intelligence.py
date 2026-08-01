from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    revision_id: str
    chunk_id: str
    dataset_id: str
    source_ref: str
    evidence_span: str = ""
    page_number: int | None = None
    text_snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None


class IntelligenceQuery(BaseModel):
    tenant_id: str
    query_text: str
    matter_id: str | None = None
    session_id: str | None = None
    dataset_ids: list[str] = Field(default_factory=list)


class IntelligenceResponse(BaseModel):
    state: OperationState
    evidence: list[Evidence] = Field(default_factory=list)
    summary: str | None = None
    error_message: str | None = None


class MesaIntelligencePort(ABC):
    @abstractmethod
    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        """
        Executes an intelligence query and returns a response.
        """
