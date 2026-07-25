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
        # PostgresLexicalAdapter requires an AsyncSession which must be
        # provided per-request via FastAPI Depends.  The factory cannot
        # supply it at module-init time, so we fall back to mock and log
        # a warning.  Use PostgresLexicalAdapter directly in endpoints
        # that inject a DB session.
        logger.warning(
            "postgres_lexical adapter requires a DB session; "
            "use PostgresLexicalAdapter(session=db) directly in endpoints. "
            "Falling back to MockMesaAdapter."
        )
        return MockMesaAdapter()
    else:
        logger.info("Initializing MockMesaAdapter")
        return MockMesaAdapter()
