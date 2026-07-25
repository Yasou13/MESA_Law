import logging
import os

from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.adapters.mock_intelligence import MockMesaAdapter
from apps.api.core.ports.intelligence import MesaIntelligencePort

logger = logging.getLogger(__name__)

def get_intelligence_adapter() -> MesaIntelligencePort:
    adapter_type = os.getenv("MESA_LAW_INTELLIGENCE_ADAPTER", "mock").lower()
    
    if adapter_type == "mesa_v4":
        logger.info("Initializing MesaV4HttpAdapter")
        return MesaV4HttpAdapter()
    elif adapter_type == "postgres_lexical":
        logger.warning(
            "postgres_lexical adapter requires a DB session; "
            "use PostgresLexicalAdapter(session=db) directly in endpoints. "
            "Falling back to MockMesaAdapter."
        )
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("Cannot fallback to MockMesaAdapter in production.")
        return MockMesaAdapter()
    else:
        if os.getenv("ENVIRONMENT") == "production" and adapter_type == "mock":
            raise RuntimeError("MockMesaAdapter is strictly prohibited in production. Set MESA_LAW_INTELLIGENCE_ADAPTER properly.")
        logger.info("Initializing MockMesaAdapter")
        return MockMesaAdapter()
