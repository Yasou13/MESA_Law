import logging

from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.adapters.mock_intelligence import MockMesaAdapter
from apps.api.core.config import settings
from apps.api.core.ports.ingestion import MesaIngestionPort
from apps.api.core.ports.intelligence import MesaIntelligencePort

logger = logging.getLogger(__name__)


def get_intelligence_adapter() -> MesaIntelligencePort:
    adapter_type = settings.intelligence_adapter.lower()

    if adapter_type == "mesa_v4":
        logger.info("Initializing MesaV4HttpAdapter")
        return MesaV4HttpAdapter()
    if adapter_type == "mock" and settings.env == "test":
        logger.info("Initializing MockMesaAdapter")
        return MockMesaAdapter()
    if adapter_type == "postgres_lexical":
        raise RuntimeError(
            "postgres_lexical requires an explicit database-scoped adapter instance"
        )
    raise RuntimeError(
        f"Intelligence adapter '{adapter_type}' is not allowed in environment '{settings.env}'"
    )


def get_ingestion_adapter() -> MesaIngestionPort:
    """Return an adapter that implements the durable MESA ingestion contract."""
    if settings.intelligence_adapter.lower() == "mesa_v4":
        logger.info("Initializing MesaV4HttpAdapter for ingestion")
        return MesaV4HttpAdapter()
    raise RuntimeError(
        "MESA ingestion requires the mesa_v4 adapter; test intelligence mocks "
        "cannot acknowledge durable publication"
    )
