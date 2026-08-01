from contextlib import ExitStack
from unittest.mock import patch

import pytest
from apps.api.core.config import settings, validate_production_settings
from apps.api.core.extraction import get_extraction_adapter
from apps.worker.core.queue import Worker


def test_mock_extraction_prohibited_in_production(monkeypatch):
    monkeypatch.setenv("MESA_LAW_EXTRACTION_ADAPTER", "mock")

    with patch.object(settings, "env", "production"):
        with pytest.raises(RuntimeError) as exc_info:
            get_extraction_adapter()
        assert "MockLegalExtractionAdapter is strictly prohibited in production" in str(
            exc_info.value
        )


def test_mock_extraction_allowed_in_development(monkeypatch):
    monkeypatch.setenv("MESA_LAW_EXTRACTION_ADAPTER", "mock")

    with patch.object(settings, "env", "development"):
        adapter = get_extraction_adapter()
        assert adapter.__class__.__name__ == "MockLegalExtractionAdapter"


def test_worker_dummy_handler_prohibited_in_production():
    worker = Worker(batch_size=1, lease_minutes=1)

    async def dummy_handler(payload, session):
        pass

    with patch.object(settings, "env", "production"):
        with pytest.raises(RuntimeError) as exc_info:
            worker.register("UNKNOWN_JOB", dummy_handler)
        assert "Dummy handlers are strictly prohibited in production" in str(
            exc_info.value
        )


def _secure_setting_patches() -> list:
    strong = "a-secure-random-value-with-more-than-32-characters"
    return [
        patch.object(settings, "env", "production"),
        patch.object(settings, "secret_key", strong),
        patch.object(settings, "keycloak_client_secret", strong),
        patch.object(settings, "storage_secret_key", strong),
        patch.object(
            settings,
            "database_url",
            f"postgresql+psycopg://mesa_law_app:{strong}@postgres/mesa_law",
        ),
        patch.object(settings, "keycloak_issuer", "https://auth.example/realms/law"),
        patch.object(
            settings,
            "keycloak_jwks_url",
            "https://auth.example/realms/law/protocol/openid-connect/certs",
        ),
        patch.object(settings, "cors_origins", ["https://law.example"]),
        patch.object(settings, "intelligence_adapter", "mesa_v4"),
        patch.object(settings, "mesa_api_key", strong),
        patch.object(settings, "clamav_required", True),
        patch.object(settings, "test_auth_enabled", False),
    ]


def test_secure_production_settings_accept_strong_external_secrets() -> None:
    with ExitStack() as stack:
        for setting_patch in _secure_setting_patches():
            stack.enter_context(setting_patch)
        validate_production_settings()


def test_secure_production_settings_reject_placeholder_storage_secret() -> None:
    with ExitStack() as stack:
        for setting_patch in _secure_setting_patches():
            stack.enter_context(setting_patch)
        stack.enter_context(
            patch.object(settings, "storage_secret_key", "replace_with_a_secret")
        )
        with pytest.raises(RuntimeError, match="placeholder secrets"):
            validate_production_settings()


def test_secure_production_settings_require_malware_scanning() -> None:
    with ExitStack() as stack:
        for setting_patch in _secure_setting_patches():
            stack.enter_context(setting_patch)
        stack.enter_context(patch.object(settings, "clamav_required", False))
        with pytest.raises(RuntimeError, match="malware scanning"):
            validate_production_settings()
