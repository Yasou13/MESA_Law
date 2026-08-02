import httpx
import pytest
import respx
from apps.api.adapters.mesa_v4_intelligence import (
    MESA_CORE_COMMIT,
    MESA_CORE_VERSION,
    MesaV4HttpAdapter,
)
from apps.api.core.ports.intelligence import IntelligenceQuery, OperationState
from apps.api.core.ports.mesa_v4 import (
    MemoryInsertRequest,
    MesaCapacityError,
    MesaConflictError,
    MesaUnavailableError,
    MutationState,
    RevisionRequest,
)


@pytest.fixture
def adapter():
    return MesaV4HttpAdapter(
        backend_url="http://mock-mesa",
        api_key="test-key",
        max_attempts=2,
    )


def test_gateway_is_pinned_to_reviewed_core_contract():
    assert MESA_CORE_VERSION == "0.7.1"
    assert MESA_CORE_COMMIT == "c5901881fc414dfd3475c386d2c59bb461e65cd2"


@pytest.mark.asyncio
@respx.mock
async def test_search_uses_exact_v4_endpoint_header_and_provenance(adapter):
    route = respx.post("http://mock-mesa/v4/memory/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "session_id": "session-1",
                "dataset_ids": ["dataset-1"],
                "results": [
                    {
                        "entity": {"entity_id": "entity-1"},
                        "rrf_score": 0.2,
                        "legal_factor": 1.1,
                        "final_score": 0.22,
                        "provenance": [
                            {
                                "tenant_id": "tenant-1",
                                "dataset_id": "dataset-1",
                                "document_id": "document-1",
                                "revision_id": "revision-1",
                                "chunk_id": "chunk-1",
                                "source_ref": "mesa-law://document-1/revision-1/chunk-1",
                                "evidence_span": "0:13",
                                "metadata": {
                                    "page_number": 5,
                                    "evidence_text": "Exact evidence",
                                },
                            }
                        ],
                    }
                ],
            },
        )
    )

    result = await adapter.query(
        IntelligenceQuery(
            tenant_id="tenant-1",
            matter_id="matter-1",
            query_text="test query",
            session_id="session-1",
            dataset_ids=["dataset-1"],
        )
    )

    assert result.state == OperationState.success
    assert result.evidence[0].revision_id == "revision-1"
    assert result.evidence[0].chunk_id == "chunk-1"
    assert result.evidence[0].page_number == 5
    assert route.calls[0].request.headers["X-API-Key"] == "test-key"
    assert route.calls[0].request.headers.get("X-Mesa-Api-Key") is None
    assert route.calls[0].request.read()
    await adapter.close()


@pytest.mark.asyncio
@respx.mock
async def test_revision_uses_exact_catalog_payload(adapter):
    route = respx.post("http://mock-mesa/v4/catalog/revisions").mock(
        return_value=httpx.Response(201, json={"revision_id": "revision-2"})
    )
    await adapter.create_revision(
        RevisionRequest(
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            dataset_id="dataset-1",
            document_id="document-1",
            revision_id="revision-2",
            revision_number=2,
            content_sha256="a" * 64,
            supersedes_revision_id="revision-1",
        )
    )

    assert route.called
    assert b'"content_sha256":"' in route.calls[0].request.content
    assert b'"supersedes_revision_id":"revision-1"' in route.calls[0].request.content
    await adapter.close()


@pytest.mark.asyncio
@respx.mock
async def test_insert_returns_admission_not_commit(adapter):
    respx.post("http://mock-mesa/v4/memory/insert").mock(
        return_value=httpx.Response(
            202,
            json={
                "status": "accepted",
                "mutation_id": "mutation-1",
                "candidate_id": "candidate-1",
                "pipeline_run_id": "pipeline-1",
                "raw_log_id": 41,
            },
        )
    )
    admission = await adapter.insert_memory(
        MemoryInsertRequest(
            session_id="session-1",
            dataset_id="dataset-1",
            document_id="document-1",
            revision_id="revision-1",
            chunk_id="chunk-1",
            title="Document 1",
            source_ref="mesa-law://document-1/revision-1/chunk-1",
            content="Exact evidence",
            idempotency_key="insert-1",
        )
    )

    assert admission.status == "accepted"
    assert admission.mutation_id == "mutation-1"
    await adapter.close()


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    ("status", "detail", "error_type"),
    [
        (409, "idempotency_key is in progress", MesaConflictError),
        (413, "queue_record_too_large", MesaCapacityError),
        (503, "queue_over_capacity", MesaUnavailableError),
    ],
)
async def test_admission_failures_are_typed(adapter, status, detail, error_type):
    respx.post("http://mock-mesa/v4/memory/insert").mock(
        return_value=httpx.Response(status, json={"detail": detail})
    )
    request = MemoryInsertRequest(
        session_id="session-1",
        dataset_id="dataset-1",
        document_id="document-1",
        revision_id="revision-1",
        chunk_id="chunk-1",
        title="Document 1",
        source_ref="source-1",
        content="Exact evidence",
        idempotency_key="insert-1",
    )

    with pytest.raises(error_type):
        await adapter.insert_memory(request)
    await adapter.close()


@pytest.mark.asyncio
@respx.mock
async def test_mutation_terminal_state_is_not_inferred_from_admission(adapter):
    respx.get("http://mock-mesa/v4/mutations/mutation-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "mutation_id": "mutation-1",
                "candidate_id": "candidate-1",
                "state": MutationState.COMMITTED,
                "artifacts": [],
                "projections": [],
            },
        )
    )

    mutation = await adapter.mutation_status("mutation-1")

    assert mutation.is_terminal is True
    assert mutation.state == "COMMITTED"
    await adapter.close()
