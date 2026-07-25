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

def get_extraction_adapter() -> LegalExtractionAdapter:
    # In a real app, this might read from config to return OpenAIAdapter, AnthropicAdapter, etc.
    return MockLegalExtractionAdapter()
