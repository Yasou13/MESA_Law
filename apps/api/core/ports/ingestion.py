from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class IngestionItem(BaseModel):
    tenant_id: str
    matter_id: str | None
    workspace_id: str | None = None
    dataset_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
    document_id: str
    revision_id: str
    chunk_id: str | None = None
    page_number: int
    text_content: str
    source_name: str
    source_type: str = "document"
    source_ref: str | None = None
    evidence_span: str = ""
    chunk_ordinal: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class MesaIngestionPort(ABC):
    @abstractmethod
    async def ingest(self, item: IngestionItem) -> bool:
        """
        Sends an ingestion item to MESA Core.
        Returns True if successful, False otherwise.
        """

    @abstractmethod
    async def rebuild_tenant(self, tenant_id: str) -> bool:
        """
        Triggers a rebuild for the tenant in MESA Core.
        """
