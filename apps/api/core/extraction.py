import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("api.extraction")

class LegalExtractionAdapter(ABC):
    @abstractmethod
    async def extract_claims(self, text: str) -> list[dict]:
        """Extract legal claims from text."""
        
    @abstractmethod
    async def extract_parties(self, text: str) -> list[dict]:
        """Extract legal parties from text."""
        
    @abstractmethod
    async def extract_events(self, text: str) -> list[dict]:
        """Extract key legal events/deadlines from text."""
        
    @abstractmethod
    async def extract_evidence(self, text: str) -> list[dict]:
        """Extract potential evidence/exhibits from text."""

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
        
    async def extract_events(self, text: str) -> list[dict]:
        logger.info("MockLegalExtractionAdapter: Extracting events")
        return [
            {
                "trigger_event": "Mock Tebliğ",
                "rule_name": "Mock Deadline 14 Days",
                "offset_days": 14,
                "description": "Mock deadline trigger."
            }
        ]
        
    async def extract_evidence(self, text: str) -> list[dict]:
        logger.info("MockLegalExtractionAdapter: Extracting evidence")
        return [
            {
                "description": "Mock Exhibit A",
                "relevance": "High"
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
    
    if adapter_type in ("llm", "enhanced"):
        from apps.api.services.legal_extraction import LLMEnhancedExtractionAdapter
        return LLMEnhancedExtractionAdapter()
    
    from apps.api.services.legal_extraction import HeuristicLegalExtractionAdapter
    return HeuristicLegalExtractionAdapter()

