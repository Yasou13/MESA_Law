"""Current sourced-QA orchestration and offline client integration tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.qa import QACitation, ask_matter_question

os.environ["MESA_LAW_ENVIRONMENT"] = "test"


def verified_citation() -> QACitation:
    return QACitation(
        document_id="doc-1",
        revision_id="rev-1",
        page_number=3,
        low_provenance=False,
        provenance_state="VERIFIED_PDF_TEXT",
        chunk_id="chunk-1",
        text_start=10,
        text_end=42,
        evidence_excerpt="Doğrulanmış sözleşme yükümlülüğü.",
        evidence_sha256="a" * 64,
    )


@pytest.mark.asyncio
async def test_test_environment_does_not_fabricate_a_qa_answer() -> None:
    session = AsyncMock()
    session.scalar.return_value = None
    empty_result = MagicMock()
    empty_result.all.return_value = []
    session.execute.return_value = empty_result

    response = await ask_matter_question(
        session, "tenant-1", "matter-1", None, "Kaynakta ne yazıyor?"
    )

    assert response.status == "ABSTAIN"
    assert response.citations == []
    assert response.degraded_reason == "MESA_SCOPE_NOT_READY"
    assert "doğrulanmış kaynak bulunamadı" in response.answer
    assert response.retrieval.scope == "MATTER"
    assert response.retrieval.engine == "NONE"
    assert response.retrieval.verified_document_count == 0


@pytest.mark.asyncio
async def test_mesa_failure_degrades_only_to_verified_local_evidence() -> None:
    binding = type(
        "Binding",
        (),
        {"provisioning_status": "READY", "dataset_id": "dataset-1"},
    )()
    session = AsyncMock()
    session.scalar.return_value = binding
    citation = verified_citation()

    with (
        patch(
            "apps.api.core.qa._mesa_citations",
            new_callable=AsyncMock,
            return_value=([], "MESA_UNAVAILABLE:MesaUnavailableError"),
        ),
        patch(
            "apps.api.core.qa._lexical_citations",
            new_callable=AsyncMock,
            return_value=[citation],
        ),
    ):
        response = await ask_matter_question(
            session, "tenant-1", "matter-1", None, "Yükümlülük nedir?"
        )

    assert response.status == "DEGRADED"
    assert response.degraded_reason == "MESA_UNAVAILABLE:MesaUnavailableError"
    assert response.citations == [citation]
    assert citation.evidence_excerpt in response.answer
    assert response.retrieval.engine == "LOCAL_FALLBACK"
    assert response.retrieval.verified_document_count == 1
    assert response.retrieval.verified_citation_count == 1


class TestLLMClient:
    """The optional LLM abstraction remains offline and mock-only in this suite."""

    def test_llm_config_from_env(self):
        from apps.api.core.llm_client import LLMProvider, get_llm_config

        with patch.dict(os.environ, {"MESA_LAW_LLM_PROVIDER": "mock"}):
            config = get_llm_config()
            assert config.provider == LLMProvider.MOCK

    def test_llm_config_unknown_provider_fallback(self):
        from apps.api.core.llm_client import LLMProvider, get_llm_config

        with patch.dict(os.environ, {"MESA_LAW_LLM_PROVIDER": "unknown_ai_provider"}):
            config = get_llm_config()
            assert config.provider == LLMProvider.MOCK

    def test_create_mock_client(self):
        from apps.api.core.llm_client import (
            LLMConfig,
            LLMProvider,
            MockLLMClient,
            create_llm_client,
        )

        client = create_llm_client(LLMConfig(provider=LLMProvider.MOCK))
        assert isinstance(client, MockLLMClient)

    @pytest.mark.asyncio
    async def test_mock_client_complete(self):
        from apps.api.core.llm_client import (
            LLMConfig,
            LLMMessage,
            LLMProvider,
            MockLLMClient,
        )

        client = MockLLMClient(LLMConfig(provider=LLMProvider.MOCK))
        response = await client.complete(
            [LLMMessage(role="user", content="Test question")]
        )

        assert "MOCK LLM" in response.content
        assert response.provider == "mock"
        assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_client_stream(self):
        from apps.api.core.llm_client import (
            LLMConfig,
            LLMMessage,
            LLMProvider,
            MockLLMClient,
        )

        client = MockLLMClient(LLMConfig(provider=LLMProvider.MOCK))
        chunks = [
            chunk
            async for chunk in client.stream([LLMMessage(role="user", content="Test")])
        ]

        assert chunks
        assert "MOCK" in "".join(chunks).strip()
