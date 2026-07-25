import httpx
import pytest
import respx
from apps.api.adapters.mesa_v4_intelligence import MesaV4HttpAdapter
from apps.api.core.ports.intelligence import IntelligenceQuery, OperationState


@pytest.fixture
def adapter():
    return MesaV4HttpAdapter(backend_url="http://mock-mesa", api_key="test-key")

@pytest.mark.asyncio
@respx.mock
async def test_mesa_v4_adapter_success(adapter):
    respx.get("http://mock-mesa/v4/capability").mock(return_value=httpx.Response(200, json={"version": "v4"}))
    
    respx.post("http://mock-mesa/v4/search").mock(return_value=httpx.Response(200, json={
        "context": "Here is the context",
        "retrieved_nodes": [
            {
                "node_id": "test-node",
                "content_payload": "This is a test node",
                "locator": {
                    "document_id": "doc123",
                    "page_number": 5
                }
            }
        ]
    }))
    
    query = IntelligenceQuery(tenant_id="tenant1", matter_id="matter1", query_text="test query")
    res = await adapter.query(query)
    
    assert res.state == OperationState.success
    assert res.summary == "Here is the context"
    assert len(res.evidence) == 1
    assert res.evidence[0].document_id == "doc123"
    assert res.evidence[0].page_number == 5
    assert res.evidence[0].text_snippet == "This is a test node"
    await adapter.close()

@pytest.mark.asyncio
@respx.mock
async def test_mesa_v4_adapter_retry_on_5xx(adapter):
    respx.get("http://mock-mesa/v4/capability").mock(return_value=httpx.Response(200, json={"version": "v4"}))
    
    # Mocking a sequence of responses: 503, then 200
    search_route = respx.post("http://mock-mesa/v4/search")
    search_route.side_effect = [
        httpx.Response(503, json={"error": "Service Unavailable"}),
        httpx.Response(200, json={
            "context": "Recovered context",
            "retrieved_nodes": []
        })
    ]
    
    query = IntelligenceQuery(tenant_id="tenant1", query_text="retry query")
    res = await adapter.query(query)
    
    assert search_route.call_count == 2
    assert res.state == OperationState.no_evidence_retrieved
    await adapter.close()

@pytest.mark.asyncio
@respx.mock
async def test_mesa_v4_adapter_auth_error(adapter):
    respx.get("http://mock-mesa/v4/capability").mock(return_value=httpx.Response(200, json={"version": "v4"}))
    
    respx.post("http://mock-mesa/v4/search").mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))
    
    query = IntelligenceQuery(tenant_id="tenant1", query_text="auth query")
    res = await adapter.query(query)
    
    assert res.state == OperationState.unavailable
    assert "Authentication failed" in res.error_message
    await adapter.close()

@pytest.mark.asyncio
@respx.mock
async def test_mesa_v4_adapter_timeout(adapter):
    respx.get("http://mock-mesa/v4/capability").mock(return_value=httpx.Response(200, json={"version": "v4"}))
    
    search_route = respx.post("http://mock-mesa/v4/search")
    search_route.side_effect = httpx.TimeoutException("Timeout from mock server")
    
    query = IntelligenceQuery(tenant_id="tenant1", query_text="timeout query")
    res = await adapter.query(query)
    
    assert res.state == OperationState.unavailable
    assert search_route.call_count == 3  # Tenacity retries on TimeoutException
    await adapter.close()
