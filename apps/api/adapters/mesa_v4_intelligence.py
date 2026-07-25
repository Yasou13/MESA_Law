import logging
from typing import Any

import httpx
from apps.api.core.config import settings
from apps.api.core.ports.ingestion import IngestionItem, MesaIngestionPort
from apps.api.core.ports.intelligence import (
    Evidence,
    IntelligenceQuery,
    IntelligenceResponse,
    MesaIntelligencePort,
    OperationState,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

class MesaV4HttpAdapter(MesaIntelligencePort, MesaIngestionPort):
    def __init__(self, backend_url: str = settings.mesa_backend_url, api_key: str = settings.mesa_api_key):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Mesa-Api-Key": self.api_key,
        }
        self.client = httpx.AsyncClient(base_url=self.backend_url, headers=self.headers, timeout=30.0)
        self._capabilities: dict[str, Any] | None = None

    async def _ensure_capabilities(self):
        if self._capabilities is None:
            try:
                response = await self.client.get("/v4/capability")
                response.raise_for_status()
                self._capabilities = response.json()
                logger.info(f"MESA Capabilities loaded: {self._capabilities}")
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Failed to fetch MESA capabilities, assuming degraded mode: {e}")
                self._capabilities = {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _post_search(self, payload: dict) -> httpx.Response:
        response = await self.client.post("/v4/search", json=payload)
        # Raise for 5xx errors to trigger retry. 
        if response.status_code >= 500:
            response.raise_for_status()
        return response

    async def query(self, query: IntelligenceQuery) -> IntelligenceResponse:
        await self._ensure_capabilities()
        
        # MESA Core expects agent_id and session_id
        # We map tenant_id to agent_id and matter_id to session_id
        payload = {
            "query": query.query_text,
            "agent_id": query.tenant_id,
            "session_id": query.matter_id or "default-session",
            "limit": 10
        }
        
        try:
            response = await self._post_search(payload)
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"Network error communicating with MESA: {e}")
            return IntelligenceResponse(
                state=OperationState.unavailable,
                error_message="MESA backend is unavailable or timed out."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Server error from MESA: {e}")
            return IntelligenceResponse(
                state=OperationState.unavailable,
                error_message="MESA backend returned a server error."
            )
            
        if response.status_code == 401 or response.status_code == 403:
            logger.error(f"Auth error from MESA: {response.status_code}")
            return IntelligenceResponse(
                state=OperationState.unavailable,
                error_message="Authentication failed with MESA backend."
            )
        elif response.status_code == 404:
            return IntelligenceResponse(state=OperationState.unavailable, error_message="MESA endpoint not found.")
        elif response.status_code == 202:
            return IntelligenceResponse(state=OperationState.pending)
        elif response.status_code != 200:
            return IntelligenceResponse(state=OperationState.unavailable, error_message=f"Unexpected status: {response.status_code}")

        data = response.json()
        retrieved_nodes = data.get("retrieved_nodes", [])
        
        if not retrieved_nodes:
            return IntelligenceResponse(
                state=OperationState.no_evidence_retrieved,
                summary="No evidence could be retrieved for this query."
            )
            
        evidence_list = []
        for node in retrieved_nodes:
            doc_id = node.get("node_id", "unknown")
            page_num = 1
            
            locator = node.get("locator")
            if locator:
                doc_id = locator.get("document_id", doc_id)
                page_num = locator.get("page_number") or 1
                
            evidence_list.append(Evidence(
                document_id=doc_id,
                page_number=page_num,
                text_snippet=node.get("content_payload", "")
            ))
            
        return IntelligenceResponse(
            state=OperationState.success,
            evidence=evidence_list,
            summary=data.get("context", "Context provided by MESA")
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _post_insert(self, payload: dict) -> httpx.Response:
        response = await self.client.post("/v4/insert", json=payload)
        if response.status_code >= 500:
            response.raise_for_status()
        return response

    async def ingest(self, item: IngestionItem) -> bool:
        await self._ensure_capabilities()
        
        # Build memory insert payload
        # idempotency_key ensures we don't index same page/revision twice
        payload = {
            "agent_id": item.tenant_id,
            "session_id": item.matter_id or "default-session",
            "source_name": item.source_name,
            "source_type": item.source_type,
            "payload": item.text_content,
            "idempotency_key": f"{item.document_id}_{item.revision_id}_{item.page_number}",
            "locator": {
                "document_id": item.document_id,
                "chunk_index": item.page_number,
                "page_number": item.page_number,
                "version_id": item.revision_id
            }
        }
        
        try:
            response = await self._post_insert(payload)
            response.raise_for_status()
            return True
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to ingest to MESA: {e}")
            return False

    async def rebuild_tenant(self, tenant_id: str) -> bool:
        await self._ensure_capabilities()
        try:
            response = await self.client.post("/v4/rebuild", json={"agent_id": tenant_id})
            response.raise_for_status()
            return True
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to rebuild MESA tenant {tenant_id}: {e}")
            return False

    async def close(self):
        await self.client.aclose()
