import logging
import os

from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.adapters.mock_intelligence import MockMesaAdapter
from apps.api.core.config import settings
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
        if settings.is_secure_environment:
            raise RuntimeError("CRITICAL: Mock adapter is strictly prohibited in pilot/production.")
        return MockMesaAdapter()
    else:
        if settings.is_secure_environment and adapter_type == "mock":
            raise RuntimeError("CRITICAL: Mock adapter is strictly prohibited in pilot/production.")
        logger.info("Initializing MockMesaAdapter")
        return MockMesaAdapter()
