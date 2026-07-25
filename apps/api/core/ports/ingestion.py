from abc import ABC, abstractmethod

from pydantic import BaseModel


class IngestionItem(BaseModel):
    tenant_id: str
    matter_id: str | None
    document_id: str
    revision_id: str
    page_number: int
    text_content: str
    source_name: str
    source_type: str = "document"
    
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
