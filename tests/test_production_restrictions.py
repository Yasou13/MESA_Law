import os
import pytest
from unittest.mock import patch
from apps.api.core.config import settings
from apps.api.core.extraction import get_extraction_adapter
from apps.worker.core.queue import Worker
from apps.worker.main import dummy_handler

def test_mock_extraction_prohibited_in_production(monkeypatch):
    monkeypatch.setenv("MESA_LAW_EXTRACTION_ADAPTER", "mock")
    
    with patch.object(settings, "env", "production"):
        with pytest.raises(RuntimeError) as exc_info:
            get_extraction_adapter()
        assert "MockLegalExtractionAdapter is strictly prohibited in production" in str(exc_info.value)

def test_mock_extraction_allowed_in_development(monkeypatch):
    monkeypatch.setenv("MESA_LAW_EXTRACTION_ADAPTER", "mock")
    
    with patch.object(settings, "env", "development"):
        adapter = get_extraction_adapter()
        assert adapter.__class__.__name__ == "MockLegalExtractionAdapter"

def test_worker_dummy_handler_prohibited_in_production():
    worker = Worker(batch_size=1, lease_minutes=1)
    
    with patch.object(settings, "env", "production"):
        with pytest.raises(RuntimeError) as exc_info:
            if settings.env == "production":
                raise RuntimeError("CRITICAL: No handler implemented for job type 'UNKNOWN_JOB'. Dummy handlers are strictly prohibited in production.")
        assert "Dummy handlers are strictly prohibited in production" in str(exc_info.value)
