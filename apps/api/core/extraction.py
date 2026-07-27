import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("api.extraction")

class LegalExtractionAdapter(ABC):
    @abstractmethod
    async def extract_claims(self, text: str) -> list[dict]:
        """Extract legal claims from text."""
        pass
        
    @abstractmethod
    async def extract_parties(self, text: str) -> list[dict]:
        """Extract legal parties from text."""
        pass

class MockLegalExtractionAdapter(LegalExtractionAdapter):
    async def extract_claims(self, text: str) -> list[dict]:
        logger.info("MockLegalExtractionAdapter: Extracting claims")
        # Dummy response
        return [
            {
                "description": "Mock claim 1 extracted from text.",
                "confidence": 0.95
            },
            {
                "description": "Mock claim 2 extracted from text.",
                "confidence": 0.88
            }
        ]
        
    async def extract_parties(self, text: str) -> list[dict]:
        logger.info("MockLegalExtractionAdapter: Extracting parties")
        # Dummy response
        return [
            {
                "name": "John Doe",
                "role": "PLAINTIFF",
                "type": "PERSON"
            },
            {
                "name": "Acme Corp",
                "role": "DEFENDANT",
                "type": "ORGANIZATION"
            }
        ]

from apps.api.core.config import settings

def get_extraction_adapter() -> LegalExtractionAdapter:
    import os
    adapter_type = os.getenv("MESA_LAW_EXTRACTION_ADAPTER", "heuristic").lower()
    if adapter_type == "mock":
        if settings.is_secure_environment:
            raise RuntimeError("CRITICAL: MockLegalExtractionAdapter is strictly prohibited in production.")
        return MockLegalExtractionAdapter()
    
    from apps.api.services.legal_extraction import HeuristicLegalExtractionAdapter
    return HeuristicLegalExtractionAdapter()
