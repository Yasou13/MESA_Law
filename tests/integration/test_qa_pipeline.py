"""
QA Pipeline Integration Tests — tests the QA answer pipeline logic
with mock LLM but exercising real retrieval paths and citation verification.
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["MESA_LAW_ENVIRONMENT"] = "test"


# ---------------------------------------------------------------------------
# QA Module Structure Tests
# ---------------------------------------------------------------------------

class TestQAModuleStructure:
    """Tests for QA module imports and structure."""

    def test_qa_module_imports(self):
        """QA module should import without errors."""
        from apps.api.core.qa import ask_matter_question, PostgresLexicalAdapter
        assert callable(ask_matter_question)
        assert PostgresLexicalAdapter is not None

    def test_qa_module_has_tiered_functions(self):
        """QA module should have the 3-tier helper functions."""
        from apps.api.core import qa
        assert hasattr(qa, "_try_mesa_intelligence")
        assert hasattr(qa, "_try_llm_augmented_answer")
        assert hasattr(qa, "_build_citations_from_chunks")


# ---------------------------------------------------------------------------
# Test Mode Short Circuit
# ---------------------------------------------------------------------------

class TestQATestMode:
    """Tests for QA test environment behavior."""

    @pytest.mark.asyncio
    async def test_test_mode_returns_mock(self):
        """In test environment, QA should return mock response."""
        with patch.dict(os.environ, {"MESA_LAW_ENVIRONMENT": "test"}):
            from apps.api.core.qa import ask_matter_question
            session = AsyncMock()
            result = await ask_matter_question(
                session, "tenant-1", "matter-1", None, "Test question?"
            )
            assert result["state"] == "MOCK_RESPONSE"
            assert "Test question?" in result["answer"]
            assert result["processing_state"] == "READY"


# ---------------------------------------------------------------------------
# Citation Building Tests
# ---------------------------------------------------------------------------

class TestCitationBuilding:
    """Tests for citation construction from retrieval results."""

    def test_build_citations_from_chunks(self):
        """Citations should be correctly built from retrieval results."""
        from apps.api.core.qa import _build_citations_from_chunks

        results = [
            {
                "document_id": "doc-1",
                "document_revision_id": "rev-1",
                "chunk_id": "chunk-1",
                "page_number": 3,
                "text": "İşçinin kıdem tazminatı hakkı bulunmaktadır." * 5,  # Long text
            },
            {
                "document_id": "doc-2",
                "document_revision_id": "rev-2",
                "chunk_id": "chunk-2",
                "page_number": 7,
                "text": "Fazla mesai ücreti hesaplanmalıdır.",
            },
        ]

        citations = _build_citations_from_chunks(results)

        assert len(citations) == 2
        assert citations[0]["document_id"] == "doc-1"
        assert citations[0]["page_number"] == 3
        assert citations[0]["verification_state"] == "verified"
        assert len(citations[0]["text_snippet"]) <= 150  # Truncated

    def test_build_citations_empty_results(self):
        """Empty results should produce empty citations."""
        from apps.api.core.qa import _build_citations_from_chunks
        assert _build_citations_from_chunks([]) == []


# ---------------------------------------------------------------------------
# LLM Augmented Answer Tests
# ---------------------------------------------------------------------------

class TestLLMAugmentedAnswer:
    """Tests for the LLM-augmented answer generation tier."""

    @pytest.mark.asyncio
    async def test_llm_augmented_skips_mock_provider(self):
        """LLM augmentation should skip when provider is mock."""
        from apps.api.core.qa import _try_llm_augmented_answer

        results = [
            {
                "document_id": "doc-1",
                "document_revision_id": "rev-1",
                "chunk_id": "chunk-1",
                "page_number": 1,
                "text": "Test content",
            }
        ]

        # With default mock provider, should return None
        result = await _try_llm_augmented_answer("test question", results)
        assert result is None

    @pytest.mark.asyncio
    async def test_llm_hallucination_guard(self):
        """LLM citations referencing non-existent documents should be filtered."""
        from apps.api.core.qa import _try_llm_augmented_answer
        from apps.api.core.llm_client import LLMResponse, LLMProvider, LLMConfig

        retrieval_results = [
            {
                "document_id": "real-doc-1",
                "document_revision_id": "rev-1",
                "chunk_id": "chunk-1",
                "page_number": 1,
                "text": "Real document content",
            }
        ]

        # Mock LLM response with a fabricated citation
        mock_llm_response = {
            "answer": "Test answer",
            "citations": [
                {"document_id": "real-doc-1", "page_number": 1, "text_snippet": "Real"},
                {"document_id": "FABRICATED-DOC", "page_number": 99, "text_snippet": "Fake"},
            ],
            "confidence": "high",
            "has_sufficient_evidence": True,
            "llm_provider": "test",
        }

        with patch("apps.api.core.qa.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.config = LLMConfig(provider=LLMProvider.OPENAI)
            mock_get_client.return_value = mock_client

            with patch("apps.api.core.qa.ask_with_llm", new_callable=AsyncMock, return_value=mock_llm_response):
                result = await _try_llm_augmented_answer("test question", retrieval_results)

                assert result is not None
                # Fabricated citation should be filtered out
                for citation in result["citations"]:
                    assert citation["document_id"] != "FABRICATED-DOC"


# ---------------------------------------------------------------------------
# MESA Intelligence Tier Tests
# ---------------------------------------------------------------------------

class TestMESAIntelligenceTier:
    """Tests for the MESA Core intelligence tier."""

    @pytest.mark.asyncio
    async def test_mesa_unavailable_returns_none(self):
        """When MESA is unavailable, tier 1 should return None gracefully."""
        from apps.api.core.qa import _try_mesa_intelligence

        with patch("apps.api.core.qa.MesaV4HttpAdapter") as MockAdapter:
            MockAdapter.side_effect = Exception("Connection refused")
            result = await _try_mesa_intelligence("tenant-1", "matter-1", "test question")
            assert result is None

    @pytest.mark.asyncio
    async def test_mesa_success_returns_response(self):
        """Successful MESA response should be returned with citations."""
        from apps.api.core.qa import _try_mesa_intelligence
        from apps.api.core.ports.intelligence import (
            Evidence,
            IntelligenceResponse,
            OperationState,
        )

        mock_response = IntelligenceResponse(
            state=OperationState.success,
            evidence=[
                Evidence(document_id="doc-1", page_number=5, text_snippet="Test evidence")
            ],
            summary="MESA found relevant evidence."
        )

        with patch("apps.api.core.qa.MesaV4HttpAdapter") as MockAdapter:
            mock_adapter_instance = AsyncMock()
            mock_adapter_instance.query.return_value = mock_response
            MockAdapter.return_value = mock_adapter_instance

            result = await _try_mesa_intelligence("tenant-1", "matter-1", "test question")

            assert result is not None
            assert result["state"] == "EVIDENCE_FOUND"
            assert len(result["citations"]) == 1
            assert result["citations"][0]["document_id"] == "doc-1"

    @pytest.mark.asyncio
    async def test_mesa_no_evidence(self):
        """MESA returning no evidence should produce appropriate response."""
        from apps.api.core.qa import _try_mesa_intelligence
        from apps.api.core.ports.intelligence import IntelligenceResponse, OperationState

        mock_response = IntelligenceResponse(
            state=OperationState.no_evidence_retrieved,
            summary="No evidence found."
        )

        with patch("apps.api.core.qa.MesaV4HttpAdapter") as MockAdapter:
            mock_adapter_instance = AsyncMock()
            mock_adapter_instance.query.return_value = mock_response
            MockAdapter.return_value = mock_adapter_instance

            result = await _try_mesa_intelligence("tenant-1", "matter-1", "test question")

            assert result is not None
            assert result["state"] == "NO_EVIDENCE_RETRIEVED"


# ---------------------------------------------------------------------------
# LLM Client Tests
# ---------------------------------------------------------------------------

class TestLLMClient:
    """Tests for the LLM client abstraction."""

    def test_llm_config_from_env(self):
        """LLM config should be built from environment variables."""
        from apps.api.core.llm_client import get_llm_config, LLMProvider

        with patch.dict(os.environ, {"MESA_LAW_LLM_PROVIDER": "mock"}):
            config = get_llm_config()
            assert config.provider == LLMProvider.MOCK

    def test_llm_config_unknown_provider_fallback(self):
        """Unknown provider should fall back to mock."""
        from apps.api.core.llm_client import get_llm_config, LLMProvider

        with patch.dict(os.environ, {"MESA_LAW_LLM_PROVIDER": "unknown_ai_provider"}):
            config = get_llm_config()
            assert config.provider == LLMProvider.MOCK

    def test_create_mock_client(self):
        """Mock client should be created for mock provider."""
        from apps.api.core.llm_client import create_llm_client, LLMConfig, LLMProvider, MockLLMClient

        config = LLMConfig(provider=LLMProvider.MOCK)
        client = create_llm_client(config)
        assert isinstance(client, MockLLMClient)

    @pytest.mark.asyncio
    async def test_mock_client_complete(self):
        """Mock LLM client should return a mock response."""
        from apps.api.core.llm_client import MockLLMClient, LLMConfig, LLMMessage, LLMProvider

        client = MockLLMClient(LLMConfig(provider=LLMProvider.MOCK))
        response = await client.complete([
            LLMMessage(role="user", content="Test question")
        ])

        assert "MOCK LLM" in response.content
        assert response.provider == "mock"
        assert response.total_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_client_stream(self):
        """Mock LLM client streaming should yield text chunks."""
        from apps.api.core.llm_client import MockLLMClient, LLMConfig, LLMMessage, LLMProvider

        client = MockLLMClient(LLMConfig(provider=LLMProvider.MOCK))
        chunks = []
        async for chunk in client.stream([LLMMessage(role="user", content="Test")]):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_text = "".join(chunks).strip()
        assert "MOCK" in full_text
